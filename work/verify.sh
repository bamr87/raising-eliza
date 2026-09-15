#!/usr/bin/env bash
# verify.sh — the whole gauntlet in one cast: trials, ledger, lore.
# Runs every gate in order; exits 0 if all pass, 1 if any fails.
set -euo pipefail

echo "=== ELIZA Verification Gauntlet ==="
echo

echo "Gate 1: Characterization Trials"
python3 -m unittest -q test_eliza
echo "✓ Trials passed"
echo

echo "Gate 2: Rosetta Ledger"
python3 reconcile.py 2>&1 | tail -2
echo "✓ Ledger passed"
echo

echo "Gate 3: Lore (Decision Records)"
python3 lore_check.py
echo "✓ Lore passed"
echo

echo "ALL GATES PASSED"
