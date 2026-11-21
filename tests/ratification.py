"""Acceptance checks for the Mullet commission and charter commands."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run(*args, check=True):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


class PublicInquiry(unittest.TestCase):
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
            source = ROOT / "tests/fixtures/constitution.json"
            compiler = ("node", "skills/mullet/scripts/charter.mjs", source, book)
            run(*compiler)
            first = book.read_bytes()
            run(*compiler)
            self.assertEqual(book.read_bytes(), first)
            run(*compiler, "17")
            self.assertEqual(book.read_text().count("sit(clerk"), 17)
            self.assertEqual(book.read_text().count("present(accounts, evidence)"), 17 * 16)


if __name__ == "__main__":
    unittest.main()
