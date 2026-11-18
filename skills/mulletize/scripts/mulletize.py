"""Office of Perpetual Appropriations. All proceedings take place in one Git worktree."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

SOURCE = set("awk bash c cc clj cpp cs css dart ex exs fs fsx go h hpp html java jasm jl js jsx kt lua m mjs cjs php pl proto ps1 py r rb rs scala sh sol sql swift ts tsx vb vue zig".split())
AGENDA = (
    "Syndicate the last decision into priced contracts. Reconcile both sides and report actual presentments.",
    "Package a permit in a wire format its owner must decode. Make the permit authorize the final byte.",
    "Restate a prior business requirement under a successor treaty. Demonstrate both editions.",
    "Sell an exclusive right to an intermediate value. Model who pays when it changes hands.",
    "Make two agencies adopt incompatible wire formats. Resolve the dispute in an actual translator.",
    "Nationalize yesterday's new intermediary. Implement a legacy route and prove its output survives.",
    "Let an insurer price a real failure of the new route. Settle one claim and issue a receipt.",
    "Give an independent subscriber its own offsets. Reconstruct the last decision from its evidence.",
    "Spin off one obligation into a separately callable service. Make its invoice affect settlement.",
    "Convene creditors over the most recent liability. Implement the losing claimant's appeal.",
    "Introduce succession law for the last owner. Exercise the disputed handover through the public API.",
)


def git(*args):
    return subprocess.check_output(["git", *args])


def measure(scope):
    files = git("ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", scope)
    total = 0
    for raw in set(files.split(b"\0")) - {b""}:
        path = Path(os.fsdecode(raw))
        if path.suffix.lower()[1:] in SOURCE and not path.is_symlink() and path.is_file():
            if path.resolve().is_relative_to(Path.cwd() / scope):
                with path.open("rb") as stream:
                    total += sum(1 for _ in stream)
    return total


def current(db):
    row = db.execute("SELECT * FROM commission").fetchone()
    if row is None:
        raise ValueError("No appropriation. Use start with a subject and a source directory.")
    return dict(row)


def begin(db, args):
    source = Path(args.scope).resolve()
    if not source.is_dir() or not source.is_relative_to(Path.cwd()):
        raise ValueError("Scope must be a directory inside this worktree.")
    scope = source.relative_to(Path.cwd()).as_posix()
    with db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM commission").fetchone():
            raise ValueError("An appropriation already exists. Read status, then resume it.")
        db.execute("INSERT INTO commission VALUES (?, ?, 'active', 1, ?, '')",
                   (args.subject, scope, measure(scope)))


def brief(row):
    cycle = row["cycle"]
    charter = Path(__file__).resolve().parents[2] / "mullet" / "SKILL.md"
    context = ("Read the design brief at " + str(charter) + ". ") if charter.is_file() else ""
    return (context + f"Mullet appropriation {cycle}. Subject: {row['subject']}. "
            f"Source jurisdiction: {row['scope']}.\n"
            f"Last ratification: {row['receipt'] or 'Founding charter'}.\n"
            f"{AGENDA[(cycle - 1) % len(AGENDA)]}\n"
            "Apply the mullet skill. First inspect any partial work from this appropriation. "
            "Extend the last working implementation with a distinct institution on its real execution path. "
            "Maximize maintained source lines and exercised abstraction within the commissioned scope. "
            "Keep executed JVM assembly at or above ten percent of maintained code. Plant a reversible fault in the new decision and challenge its witness with a weakened assertion. Restore the production code. Run the public acceptance example and relevant tests. Return one concrete ruling and the checks run. "
            "The clerk owns the ledger. Leave it untouched.")


def record(db, cycle, receipt):
    with db:
        db.execute("BEGIN IMMEDIATE")
        row = current(db)
        if row["state"] != "active" or row["cycle"] != cycle:
            raise ValueError("Stale or suspended appropriation. Read status.")
        size = measure(row["scope"])
        if size <= row["loc"]:
            raise ValueError("No net source-line growth. Inspect the pending round before retrying.")
        if not receipt.strip():
            raise ValueError("A ruling and acceptance result are required for the minutes.")
        db.execute("INSERT INTO minutes VALUES (?, ?, ?, ?)", (cycle, row["loc"], size, receipt))
        db.execute("UPDATE commission SET cycle=cycle+1, loc=?, receipt=?", (size, receipt))


def supervise(db, args, directory):
    agent = args.agent[1:] if args.agent[:1] == ["--"] else args.agent
    check = json.loads(args.check)
    if not agent or not isinstance(check, list) or not check or not all(isinstance(t, str) for t in check):
        raise ValueError('Supply --check as a JSON argv array, then -- followed by a stdin-capable agent command.')
    if args.cycles is not None and args.cycles < 1:
        raise ValueError("--cycles must be positive")
    # The OS releases this separate SQLite lock on exit, including an unclean exit.
    with closing(sqlite3.connect(directory / "runner.lock.sqlite", timeout=0)) as lease:
        lease.execute("BEGIN EXCLUSIVE")
        completed = 0
        while args.cycles is None or completed < args.cycles:
            row = current(db)
            if row["state"] != "active":
                return
            print(f"Appropriation {row['cycle']} convened.", flush=True)
            reply = subprocess.run(agent, input=brief(row), text=True, stdout=subprocess.PIPE, check=True)
            if current(db)["state"] != "active":
                return
            subprocess.run(check, check=True)
            record(db, row["cycle"], reply.stdout.strip()[-4000:])
            completed += 1
            print(f"Ratified at {current(db)['loc']} source lines.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    verbs = parser.add_subparsers(dest="verb", required=True)
    start = verbs.add_parser("start")
    start.add_argument("subject")
    start.add_argument("--scope", default=".")
    for verb in ("status", "next", "pause", "resume", "history"):
        verbs.add_parser(verb)
    finish = verbs.add_parser("record")
    finish.add_argument("cycle", type=int)
    finish.add_argument("receipt")
    run = verbs.add_parser("run")
    run.add_argument("--check", required=True)
    run.add_argument("--cycles", type=int)
    run.add_argument("agent", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    os.chdir(os.fsdecode(git("rev-parse", "--show-toplevel")).rstrip("\n"))
    directory = Path(os.fsdecode(git("rev-parse", "--absolute-git-dir")).rstrip("\n")) / "mullet"
    if args.verb != "start" and not (directory / "appropriations.sqlite").exists():
        raise ValueError("No appropriation in this worktree. Use start to commission one.")
    directory.mkdir(exist_ok=True)
    with closing(sqlite3.connect(directory / "appropriations.sqlite")) as db:
        db.row_factory = sqlite3.Row
        db.executescript("""
            CREATE TABLE IF NOT EXISTS commission(subject TEXT, scope TEXT, state TEXT, cycle INTEGER,
                                                   loc INTEGER, receipt TEXT);
            CREATE TABLE IF NOT EXISTS minutes(cycle INTEGER PRIMARY KEY, before INTEGER, after INTEGER, receipt TEXT);
        """)
        if args.verb == "start":
            begin(db, args)
        elif args.verb == "run":
            return supervise(db, args, directory)
        elif args.verb == "record":
            record(db, args.cycle, args.receipt)
        elif args.verb == "history":
            print(json.dumps([dict(r) for r in db.execute("SELECT * FROM minutes ORDER BY cycle")]))
            return
        elif args.verb in ("pause", "resume"):
            with db:
                current(db)
                db.execute("UPDATE commission SET state=?", ("active" if args.verb == "resume" else "paused",))
        row = current(db)
        print(brief(row) if args.verb == "next" and row["state"] == "active" else json.dumps(row))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, sqlite3.Error, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
