"""Use real worker processes in disposable worktrees. Never start an agent subscription."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

MULLETIZE = Path(__file__).resolve().parents[1] / 'skills/mulletize/scripts/mulletize.py'


class Appropriations(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        self.app = self.root / 'app'
        self.app.mkdir()
        (self.app / 'value.py').write_text('def answer(): return 42\n')
        self.clerk('start', 'Underwrite the integer', '--scope', 'app')

    def clerk(self, *args, ok=True):
        return subprocess.run([sys.executable, MULLETIZE, *args], cwd=self.root, capture_output=True, text=True, check=ok)

    def supervisor(self, worker, *options, check=None):
        verification = check or [sys.executable, '-c',
            "import sys; sys.path.insert(0,'app'); from value import answer; assert answer() == 42"]
        return self.clerk('run', '--check', json.dumps(verification), *options,
                          '--', sys.executable, '-c', worker, ok=False)

    def test_headless_restart_and_positive_growth(self):
        worker = """
import sys
from pathlib import Path
brief = sys.stdin.read()
assert 'Underwrite the integer' in brief
p = Path('app/value.py')
old = p.read_text()
number = old.count('def ')
p.write_text(old.replace('def answer():', f'def predecessor_{number}():') +
             f'def answer(): return predecessor_{number}()\\n')
print('The integer was underwritten. Public answer is 42.')
"""
        reply = self.supervisor(worker, '--cycles', '3')
        self.assertEqual(reply.returncode, 0, reply.stderr)
        history = json.loads(self.clerk('history').stdout)
        self.assertEqual([(r['before'], r['after']) for r in history], [(1, 2), (2, 3), (3, 4)])
        self.assertNotEqual(self.clerk('record', '3', 'Duplicate payment', ok=False).returncode, 0)
        self.assertNotEqual(self.supervisor("print('No work')", '--cycles', '1').returncode, 0)
        self.assertNotEqual(self.supervisor(worker, '--cycles', '1',
                            check=[sys.executable, '-c', 'raise SystemExit(1)']).returncode, 0)
        self.assertEqual(json.loads(self.clerk('status').stdout)['cycle'], 4)
        self.clerk('pause')
        self.assertEqual(json.loads(self.clerk('next').stdout)['state'], 'paused')
        self.clerk('resume')
        self.assertIn('Appropriation'.lower(), self.clerk('next').stdout.lower())
        self.clerk('record', '4', 'Reconciled pending change and checked answer')

    def test_open_ended_runner_obeys_pause(self):
        worker = f"""
from pathlib import Path
import subprocess, sys
p = Path('app/new.py')
with p.open('a') as f: f.write('rate = 1\\n')
if len(p.read_text().splitlines()) == 3:
    subprocess.run([sys.executable, {str(MULLETIZE)!r}, 'pause'], check=True)
print('A rate has vested.')
"""
        self.assertEqual(self.supervisor(worker).returncode, 0)
        self.assertEqual(len(json.loads(self.clerk('history').stdout)), 2)
        self.assertEqual(json.loads(self.clerk('status').stdout)['state'], 'paused')


if __name__ == '__main__':
    unittest.main()
