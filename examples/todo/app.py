"""HM Land Registry for Things You Said You Would Do."""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import unicodedata

HERE = Path(__file__).resolve().parent


def notarize(action, key, subject, previous, catalogue=None):
    petition = {"topic": "fridge.deeds.v1", "action": action, "parcel": key,
                "subject": subject, "previous": previous}
    if catalogue is not None:
        petition["catalogue"] = catalogue
    reply = subprocess.run(["node", str(HERE / "notary.mjs")], input=json.dumps(petition),
                           text=True, capture_output=True)
    if reply.returncode:
        raise RuntimeError(reply.stderr.strip())
    return json.loads(reply.stdout)


def identify_composition(title):
    normalized = unicodedata.normalize("NFKC", title or "").casefold()
    return " ".join(normalized.split())


def clear_back_catalogue(ledger, artist):
    # A pre-registry title can own the master without ever having been marked done.
    ledger.execute("""
        INSERT INTO songs(drawer, composition)
        SELECT tasks.id, identify_composition(tasks.title) FROM tasks
        LEFT JOIN songs ON songs.drawer = tasks.id WHERE songs.drawer IS NULL
    """)
    song = ledger.execute("SELECT composition FROM songs WHERE drawer=?", (artist,)).fetchone()
    master = ledger.execute("SELECT min(drawer) FROM songs WHERE composition=?", (song["composition"],)).fetchone()[0]
    return {"artist": str(artist), "master": str(master), "composition": song["composition"]}


def register_pressing(ledger, serial, pressing):
    ledger.execute("""
        INSERT INTO pressings(artist, master, serial, matrix, edition, token, gross, writer_royalty,
                              artist_share, pressing_fee, plant, award, hearings, contracts)
        VALUES (:artist, :master, :serial, :matrix, :edition, :token, :gross, :writerRoyalty,
                :artistShare, :pressingFee, :plant, :award, :hearings, :contracts)
    """, dict(pressing, serial=serial))


def record(ledger, action, key, subject):
    latest = ledger.execute("SELECT serial FROM deeds ORDER BY folio DESC LIMIT 1").fetchone()
    previous = latest["serial"] if latest else "THE FRIDGE WAS EMPTY"
    catalogue = clear_back_catalogue(ledger, key) if action == "done" else None
    deed = notarize(action, key, subject, previous, catalogue)
    if deed["pressing"]:
        register_pressing(ledger, deed["serial"], deed["pressing"])
    for easement in deed["transfer"]["contracts"]:
        ledger.execute("INSERT INTO easements(task_id, diagonal, lessor, rent) VALUES (?, ?, ?, ?)",
                       (key, easement["easement"], easement["name"], easement["rent"]))
    ledger.execute("""
        INSERT INTO deeds(task_id, action, previous, instrument, serial, seal,
                          hearings, consideration, dissent)
        VALUES (:key, :action, :previous, :instrument, :serial, :seal,
                :hearings, :consideration, :dissent)
    """, dict(deed, key=key, action=action, previous=previous))
    plan = deed["prospectus"]
    ledger.execute("INSERT INTO fiscal_supplements VALUES (?, ?, ?, ?)",
                   (deed["serial"], plan["contracts"], plan["forecast"], plan["quarters"][3]))


def transact(ledger, args):
    action = args.action
    if action == "add":
        key = ledger.execute("INSERT INTO tasks(title) VALUES (?)", (args.title,)).lastrowid
        record(ledger, action, key, args.title)
        return [f"Filed #{key}"]
    if action == "list":
        notarize(action, None, "Application to look at the fridge", "PUBLIC GALLERY")
        rows = ledger.execute("SELECT * FROM fridge_door ORDER BY id")
        return [f"{r['cartouche']} {r['id']} {r['title']}" for r in rows]
    task = ledger.execute("SELECT * FROM tasks WHERE id=?", (args.id,)).fetchone()
    if not task:
        raise ValueError(f"Unknown task #{args.id}")
    if action == "done":
        if not task["done"]:
            record(ledger, action, args.id, task["title"])
        return [f"Discharged #{args.id}"]
    notarize(action, args.id, task["title"], "PUBLIC GALLERY")
    result = [f"REGISTER OF TITLE • Drawer {args.id} • {task['title']}"]
    for deed in ledger.execute("SELECT * FROM deeds WHERE task_id=? ORDER BY folio", (args.id,)):
        result.extend([f"Folio {deed['folio']}. {deed['instrument']}.",
                       f"  {deed['hearings']} hearings. Consideration: {deed['consideration']} cents.",
                       f"  Minority opinion: {deed['dissent']}",
                       f"  Previous title: {deed['previous']}", f"  Recorded title: {deed['serial']}"])
        supplement = ledger.execute("SELECT * FROM fiscal_supplements WHERE deed_serial=?",
                                    (deed["serial"],)).fetchone()
        if supplement:
            result.append(f"  Underwritten by {supplement['settled_contracts']} contracts. "
                          f"Q4 forecast: {supplement['forecast']} cents. Realized: {supplement['realized']}.")
    for lease in ledger.execute("SELECT * FROM easements WHERE task_id=? ORDER BY diagonal", (args.id,)):
        result.append(f"  {lease['diagonal']} diagonal leased from {lease['lessor']} at {lease['rent']} cents.")
    if len(result) == 1:
        result.append("Title acquired by customary use before the invention of the Registry.")
    single = ledger.execute("SELECT * FROM pressings WHERE artist=?", (args.id,)).fetchone()
    if single:
        result.extend([f"  KITCHEN SINGLES CHART • {single['edition']} pressing • master held by drawer #{single['master']}",
                       f"  {single['award']}",
                       f"  {single['gross']} cents received: writer {single['writer_royalty']}, "
                       f"performer {single['artist_share']}, {single['plant']} {single['pressing_fee']}.",
                       f"  Release committee: {single['hearings']} hearings, {single['contracts']} contracts.",
                       f"  Runout matrix: {single['matrix']}"])
    income = ledger.execute("SELECT count(*), sum(writer_royalty) FROM pressings "
                            "WHERE master=? AND edition='cover'", (args.id,)).fetchone()
    if income[0]:
        format_name = "cover pressing" if income[0] == 1 else "cover pressings"
        result.append(f"  Publishing statement: {income[0]} {format_name}. {income[1]} cents due to this drawer.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("mullet.sqlite3"))
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("add").add_argument("title")
    commands.add_parser("list")
    for action in ("done", "history"):
        commands.add_parser(action).add_argument("id", type=int)
    args = parser.parse_args()
    with sqlite3.connect(args.db) as ledger:
        ledger.row_factory = sqlite3.Row
        ledger.create_function("identify_composition", 1, identify_composition)
        ledger.execute("PRAGMA foreign_keys=ON")
        ledger.executescript((HERE / "land-register.sql").read_text())
        ledger.execute("BEGIN IMMEDIATE" if args.action in ("add", "done") else "BEGIN")
        try:
            lines = transact(ledger, args)
        except ValueError as error:
            parser.error(str(error))
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
