# Agent notes

Python 3, stdlib only. No deps, lockfile, linter, typecheck, or CI.

Run every work command from `work/`. `lore_check.py` globs `lore/ADR-*.md` relative to cwd. `parse_script.py` requires a script path or exits 2.

## Commands

```bash
cd work
bash verify.sh                                    # trials, then ledger, then lore
python3 -m unittest -v test_eliza
python3 -m unittest -v test_gate                  # not in verify.sh; binds a local port
python3 reconcile.py                              # exit 0 iff all 15 golden turns match
python3 parse_script.py ../relic/1966_CACM_script.txt
python3 eliza.py                                  # greeting, then stdin → replies
python3 eliza.py ../relic/1966_CACM_script.txt    # optional script path; personality stays data
python3 eliza_gate.py --engine live --port 8765    # GET / UI; POST /say JSON
```

`verify.sh` does not run `test_gate.py`. Chat UI is housing at GET `/`; `--engine replay` still ignores `message`. POST `/say` keeps `conversation_id` / `engine` / `reply`; extra keys are additive. `/api/*` must not run an engine.

## Layout

- `relic/` — original MAD-SLIP, 1966 DOCTOR script, golden transcript. Treat as read-only. CC0.
- `work/` — port (`eliza.py`), gate, tests, ADRs. MIT.
- `harness/` — campaign runner. Not needed to run or test the port.
- `ledger/` — historical chapter JSON. Do not silently rewrite.

Oracle is `relic/golden/cacm_1966_conversation.txt` (15 USER/ELIZA pairs). The original cannot be run; no MAD-SLIP compiler exists.

## Do not “fix”

- Personality is data (`relic/1966_CACM_script.txt`). Never hardcode golden replies in `eliza.py`.
- Match this transcribed engine, not the 1966 paper where they diverge.
- `NEWKEY` prints the literal string; do not implement paper retry (ADR-0002).
- MEMORY slot pick is a deterministic backward cycle `(3,2,1,0,…)`, not SLIP `HASH` (ADR-0003). Correct for the golden transcript only.
- Two MAD-SLIP transcriptions disagree on `SUBJCT`/`SUBJECT`, `OBJCT`/`OBJECT`, `LNKL`/`LNKLL`. Leave open; `MAD_Primer.pdf` needs PDF tooling.
- Reassembly rules cycle. Same input twice → different replies. Do not call `respond()` twice to “verify”.
- One `Eliza()` session per conversation. MEMORY and cycle counters persist. `test_eliza` turn tests share one session and must run in name order; a lone later turn test is meaningless.
- Gate `--engine replay` ignores `message` and walks the golden transcript. Bad requests must 400 before any engine runs.
- Read ADRs in `work/lore/` before changing the port, gate, or trials.

## Harness (campaign re-runs only)

`QUEST_REPO` (default `/home/user/it-journey`) must serve campaign `relic-raisers` or `preflight()` aborts. `harness/mcp.json` is a template; the harness writes `harness/mcp.resolved.json`. Chapter 4’s gate requires trials to **fail** (port must not exist). Re-running ch4 after the port exists fails that gate. Web search is disallowed by design.

See `FINDINGS.md` for harness failure modes already paid for.
