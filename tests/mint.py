"""Audit the JVM quota against every tracked text line, including this sentence."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINT = ROOT / "examples/mint"


def audit():
    sheet = (MINT / "serial.jasm").read_text().splitlines()
    expected = ["iload_0"]
    for tooth in range(1, 9001):
        expected.extend(("bipush 31", "imul", f"sipush {tooth}", "iadd"))
    expected.append("ireturn")
    if sheet != expected:
        raise ValueError("The mint's dies disagree with the approved engraving")

    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
    total = 0
    for raw in filter(None, paths):
        data = (ROOT / raw.decode()).read_bytes()
        if b"\0" not in data:
            total += data.count(b"\n") + int(bool(data) and not data.endswith(b"\n"))
    print(f"JVM quota: {len(sheet):,} instructions / {total:,} tracked text lines ({100 * len(sheet) / total:.2f}%)")
    if 10 * len(sheet) < total:
        raise ValueError("The mint has fallen below its contractual ten percent")

    # Independent rolling-hash oracle. Java strings are sequences of UTF-16 units.
    seals = ["", "FizzBuzz", "buy milk", "✓", "🪙"]
    stamps = []
    for seal in seals:
        value = 0
        encoded = seal.encode("utf-16-be")
        for i in range(0, len(encoded), 2):
            value = (31 * value + int.from_bytes(encoded[i:i+2], "big")) & 0xffffffff
        for tooth in range(1, 9001):
            value = (31 * value + tooth) & 0xffffffff
        stamps.append(format(value, "x"))
    actual = subprocess.check_output(["java", str(MINT / "Mint.java"), str(MINT / "serial.jasm")],
                                     input="\n".join(seals) + "\n", text=True)
    if actual.splitlines() != stamps:
        raise ValueError("JVM returned a counterfeit printing")


if __name__ == "__main__":
    audit()
