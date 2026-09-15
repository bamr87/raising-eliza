#!/usr/bin/env python3
"""reconcile.py -- the Rosetta Ledger for the ELIZA port.

Runs eliza.py as one continuous session over every USER line in the golden
master (relic/golden/cacm_1966_conversation.txt), compares each reply to
the published ELIZA line turn by turn, and prints a table. Exits 0 only if
every turn ties out; exits 1 (non-zero) on any mismatch.

Usage: reconcile.py [GOLDEN_FILE] [SCRIPT_FILE]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GOLDEN = os.path.join(HERE, "..", "relic", "golden", "cacm_1966_conversation.txt")

sys.path.insert(0, HERE)
from eliza import Eliza, DEFAULT_SCRIPT_PATH  # noqa: E402


def load_golden(path):
    with open(path) as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    pairs = []
    for i in range(0, len(lines), 2):
        u_speaker, _, u_text = lines[i].partition(": ")
        e_speaker, _, e_text = lines[i + 1].partition(": ")
        assert u_speaker == "USER" and e_speaker == "ELIZA", (
            f"golden master out of order at line {i + 1}: {lines[i]!r}, {lines[i + 1]!r}"
        )
        pairs.append((u_text, e_text))
    return pairs


def main(golden_path=DEFAULT_GOLDEN, script_path=DEFAULT_SCRIPT_PATH):
    pairs = load_golden(golden_path)
    session = Eliza(script_path)

    print(f"{'#':>3}  {'USER':<48} {'RELIC':<45} {'PORT':<45}  TIES OUT")
    mismatches = 0
    for n, (user_text, expected) in enumerate(pairs, start=1):
        actual = session.respond(user_text)
        ok = actual == expected
        mismatches += 0 if ok else 1
        print(f"{n:>3}  {user_text[:48]:<48} {expected[:45]:<45} {actual[:45]:<45}  {'yes' if ok else 'NO'}")

    print()
    print(f"turns compared: {len(pairs)}   mismatches: {mismatches}")
    print("RECONCILED -- the ledger ties out." if not mismatches
          else f"NOT RECONCILED -- {mismatches} turn(s) differ.")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    argv = sys.argv[1:]
    sys.exit(main(*argv))
