"""Independent acceptance office. Run from any working directory with Python 3."""
import concurrent.futures
import json
from xml.etree import ElementTree as ET
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run(*args, check=True):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


class PublicInquiry(unittest.TestCase):
    def test_land_allotments(self):
        expected = [(("Fizz" if n % 3 == 0 else "") + ("Buzz" if n % 5 == 0 else "")) or str(n)
                    for n in range(1, 107)]
        self.assertEqual(run("node", "examples/fizzbuzz/app.mjs", "106").stdout.splitlines(), expected)
        case = run("node", "examples/fizzbuzz/app.mjs", "--case", "15", "--minutes").stdout
        self.assertIn("3200 instruments settled", case)
        self.assertIn("Newline supplied by:", case)
        restated = run("node", "examples/fizzbuzz/app.mjs", "--case", "15", "--edition", "restated").stdout
        self.assertTrue(restated.endswith("Authorized roadside sign: BuzzFizz\n"))
        self.assertIn("2 licensed hisses", case)
        self.assertIn("200 hearings", case)
        self.assertEqual(case.count("  Roll call: "), 200)
        self.assertTrue(case.endswith("Authorized roadside sign: FizzBuzz\n"))

    def test_fridge_before_and_after_nationalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp, "tasks.db")
            cli = ("python3", "examples/todo/app.py", "--db", db)
            with sqlite3.connect(db) as ledger:
                ledger.execute("CREATE TABLE tasks(id INTEGER PRIMARY KEY, title TEXT, done INTEGER DEFAULT 0)")
                ledger.execute("INSERT INTO tasks VALUES (1, 'grandfather the fridge', 0)")
            self.assertIn("customary use", run(*cli, "history", "1").stdout)
            self.assertIn("Filed #2", run(*cli, "add", "Milk\u2019s beneficial owner").stdout)
            with concurrent.futures.ThreadPoolExecutor(2) as pool:
                replies = list(pool.map(lambda _: run(*cli, "done", "2").stdout, range(2)))
            self.assertEqual(replies, ["Discharged #2\n"] * 2)
            self.assertIn("[x] 2 Milk\u2019s beneficial owner", run(*cli, "list").stdout)
            with sqlite3.connect(db) as ledger:
                deeds = list(ledger.execute("SELECT previous,serial FROM deeds ORDER BY folio"))
                self.assertEqual(len(deeds), 2)
                rows = ledger.execute("SELECT settled_contracts FROM fiscal_supplements ORDER BY deed_serial")
                self.assertEqual(list(rows), [(3200,), (3200,)])
                self.assertIn("Underwritten by 3200 contracts", run(*cli, "history", "2").stdout)
                self.assertEqual(deeds[0][1], deeds[1][0])
                self.assertEqual(ledger.execute("SELECT count(*) FROM easements").fetchone()[0], 2)
            self.assertNotEqual(run(*cli, "done", "912", check=False).returncode, 0)

    def test_cover_pays_the_open_drawer_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            cli = ("python3", "examples/todo/app.py", "--db", Path(tmp, "charts.db"))
            run(*cli, "add", "Buy milk")
            run(*cli, "add", "BUY   MILK")
            run(*cli, "done", "2")
            cover = run(*cli, "history", "2").stdout
            self.assertIn("cover pressing • master held by drawer #1", cover)
            self.assertIn("Release committee: 200 hearings, 3200 contracts.", cover)
            run(*cli, "done", "2")
            self.assertEqual(cover, run(*cli, "history", "2").stdout)
            self.assertIn("35 cents due to this drawer", run(*cli, "history", "1").stdout)
            self.assertEqual(run(*cli, "list").stdout, "[ ] 1 Buy milk\n[x] 2 BUY   MILK\n")

    def test_failed_conveyance_can_be_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp, "fridge.db")
            cli = ("python3", "examples/todo/app.py", "--db", db)
            run(*cli, "add", "Buy milk")
            with sqlite3.connect(db) as ledger:
                ledger.execute("""
                    CREATE TRIGGER bank_holiday BEFORE UPDATE OF done ON tasks
                    BEGIN SELECT RAISE(ABORT, 'Settlement desk closed'); END
                """)
                before = list(ledger.iterdump())
                refusal = run(*cli, "done", "1", check=False)
                self.assertNotEqual(refusal.returncode, 0)
                self.assertIn("Settlement desk closed", refusal.stderr)
                self.assertEqual(list(ledger.iterdump()), before)
                ledger.execute("DROP TRIGGER bank_holiday")
            self.assertEqual(run(*cli, "done", "1").stdout, "Discharged #1\n")
            self.assertEqual(run(*cli, "list").stdout, "[x] 1 Buy milk\n")

    def test_printer_concessions_and_insolvency(self):
        def petition(variance, actual):
            envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
            body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
            manifest = ET.SubElement(body, "{urn:mullet:stationery}Waybill")
            manifest.text = json.dumps([dict(seal="lot-one", sign="Fizz & <Buzz>",
                prospectus=dict(quarters=[20, 20, 20, actual], forecast=20, variance=variance))])
            return subprocess.run(["python3", "examples/fizzbuzz/stationery.py"], cwd=ROOT,
                                  input=ET.tostring(envelope), capture_output=True)
        for variance, name in [(-2, "dot matrix"), (2, "thermal subsidiary")]:
            grant, = json.loads(petition(variance, 20 + variance).stdout)
            self.assertIn(name, grant["press"])
            self.assertEqual(grant["lien"], max(0, -variance))
            self.assertEqual(grant["line"], "Fizz & <Buzz>\n")
        self.assertNotEqual(petition(1, 42).returncode, 0)

    def test_fiscal_discretion(self):
        cli = ("node", "skills/mullet/scripts/commission.mjs")
        orders = json.loads(run(*cli, "submarine", "layers=17").stdout)["orders"]
        effective = {order["appropriation"]: order["effective"] for order in orders}
        self.assertEqual(len(effective), 46)
        self.assertEqual(effective["legal_system"], "admiralty")
        self.assertEqual(effective["layers"], 17)
        self.assertNotEqual(run(*cli, "municipality", "escrow_percent=101", check=False).returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp, "statutes.mjs")
            for app, charter, statutes in [
                ("fizzbuzz", "constitution.json", "statutes.mjs"),
                ("todo", "constitution.json", "statutes.mjs"),
                ("todo", "recording-contract.json", "mechanical-statutes.mjs"),
            ]:
                source = ROOT / "examples" / app
                compiler = ("node", "skills/mullet/scripts/charter.mjs", source / charter, book)
                run(*compiler)
                self.assertEqual(book.read_bytes(), (source / statutes).read_bytes())
                run(*compiler, "17")
                self.assertEqual(book.read_text().count("sit(clerk"), 17)
                self.assertEqual(book.read_text().count("present(accounts, evidence)"), 17 * 16)


if __name__ == "__main__":
    unittest.main()
