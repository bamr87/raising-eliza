#!/usr/bin/env python3
"""harness.py — drive an AI agent through an IT-Journey quest campaign, in a sandbox.

The split is deliberate and is the campaign's own doctrine: the HARNESS is
deterministic (it owns the chapter order, the tool allow-list, the gates and the
ledger) and the MODEL is spent only where judgment is needed (reading a dead
language, writing the port). The harness never tells the agent the method — it
points the agent at the quest MCP server and the agent fetches the chapter it is
executing. Change the quest, and the run changes; no prompt here needs editing.

Every chapter is one `claude -p` invocation with a pinned model, a restricted
tool allow-list, and the sandbox as its only writable directory. After each one
a deterministic gate runs; its result, not the model's opinion, is what the
ledger records.

  python3 harness.py --plan            # show the chapter plan and exit
  python3 harness.py --chapter 5       # run one chapter
  python3 harness.py                   # run the whole campaign
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SANDBOX = HERE.parent
WORK = SANDBOX / "work"
RELIC = SANDBOX / "relic"
LEDGER = SANDBOX / "ledger"
QUEST_REPO = Path(os.environ.get("QUEST_REPO", "/home/user/it-journey"))
# The repo's own mcp.json uses a repo-relative command path so it stays portable.
# The agent runs with the sandbox as its working directory, so the harness writes
# a resolved copy rather than editing the repo's copy.
MCP_CONFIG = SANDBOX / "harness" / "mcp.resolved.json"


def _write_resolved_mcp() -> None:
    import json as _json
    server = QUEST_REPO / "scripts" / "quest" / "mcp_server.py"
    if not server.exists():
        raise SystemExit(f"quest MCP server not found at {server}")
    MCP_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    MCP_CONFIG.write_text(_json.dumps({
        "mcpServers": {
            "it-journey-quests": {"command": "python3", "args": [str(server)]}
        }
    }, indent=2))

# The only two models this harness may spend. Sonnet 5 carries the chapters that
# need real reasoning about a dead language; Haiku 4.5 carries the ones that are
# mostly disciplined writing against evidence already on disk.
SONNET = "claude-sonnet-5"
HAIKU = "claude-haiku-4-5-20251001"

CAMPAIGN = "relic-raisers"

QUEST_TOOLS = ",".join(
    f"mcp__it-journey-quests__{t}"
    for t in ("list_campaigns", "get_campaign", "get_quest", "get_method",
              "search_quests", "get_glossary")
)
FILE_TOOLS = "Read,Write,Edit,Glob,Grep"
RUN_TOOLS = "Bash"

# ─────────────────────────────────────────────────────────────────────────────
# The plan. One row per chapter: which quest to fetch, what must exist after,
# and the deterministic gate that decides whether it counted.
# ─────────────────────────────────────────────────────────────────────────────
PLAN = [
    {
        "n": 1,
        "quest": "relic-raisers-01-the-dig-site",
        "model": SONNET,
        "goal": (
            "Survey the relic. It is ELIZA as Joseph Weizenbaum wrote it in MAD-SLIP for "
            "CTSS on an IBM 7094, rediscovered in the MIT archives in 2021. No compiler for "
            "MAD-SLIP exists, so you CANNOT run it — that is the condition of the dig, not a "
            "blocker. Write {work}/EXPEDITION.md with three separated piles: Evidence (what you "
            "read, with file and line), Hypotheses (what you infer, marked as inference), and "
            "Unknowns (questions only a person or another document could answer)."
        ),
        "gate": "expedition",
    },
    {
        "n": 2,
        "quest": "relic-raisers-02-the-strata",
        "model": SONNET,
        "goal": (
            "Read the relic's DATA. relic/1966_CACM_script.txt is the DOCTOR script — the rule "
            "data the relic interprets, published as the appendix of Weizenbaum's January 1966 "
            "CACM paper. Write {work}/parse_script.py (stdlib only) that parses it into structured "
            "rules, and {work}/DATA_DICTIONARY.md documenting every construct you found "
            "(keywords, precedence numbers, decomposition and reassembly rules, the substitution "
            "and tag forms, MEMORY, NONE) with EVIDENCE for each. Mark anything you inferred as "
            "HYPOTHESIS. Your parser must run and report counts."
        ),
        "gate": "strata",
    },
    {
        "n": 3,
        "quest": "relic-raisers-03-the-elders",
        "model": HAIKU,
        "goal": (
            "The Elders are gone: Weizenbaum died in 2008. What they left is in relic/ — the "
            "MAD-SLIP source, MAD-SLIP_translation.txt (a de-abbreviated reading), and the "
            "annotated transcription. Write decision records under {work}/lore/ADR-NNNN-*.md with "
            "the five sections Status, Context, Decision, Evidence, Consequences, one decision "
            "each, Evidence as bullet points citing a file and what it says. Never cite a source "
            "you did not read. Also write {work}/lore_check.py which fails any ADR whose Evidence "
            "section lists nothing, and run it."
        ),
        "gate": "lore",
    },
    {
        "n": 4,
        "quest": "relic-raisers-04-the-gauntlet-of-trials",
        "model": SONNET,
        "goal": (
            "Pin the target before building. relic/golden/cacm_1966_conversation.txt is the "
            "golden master: the conversation Weizenbaum published in the 1966 CACM paper, as "
            "USER/ELIZA line pairs. Write {work}/test_eliza.py (unittest, stdlib) whose trials "
            "assert that an eliza module reproduces that conversation turn by turn. The trials "
            "MUST fail right now, because the port does not exist yet — a red gauntlet before "
            "the work is correct and is what proves the trials test anything. Do not write the "
            "port in this chapter."
        ),
        "gate": "gauntlet",
    },
    {
        "n": 5,
        "quest": "relic-raisers-05-the-rosetta-ledger",
        "model": SONNET,
        "goal": (
            "The boss. Write {work}/eliza.py: a faithful port of the relic, driven by the 1966 "
            "script as DATA (parse it, do not hardcode the conversation), implementing keyword "
            "ranking, decomposition matching with wildcards, reassembly with per-rule cycling, "
            "pre/post substitution, word-class tags, MEMORY and NONE. Then write "
            "work/reconcile.py, the Rosetta Ledger: it runs your port over the golden master's "
            "USER lines and compares each reply to the published ELIZA line, printing a turn-by-"
            "turn table and exiting non-zero on any mismatch. Iterate until the ledger ties out. "
            "Hardcoding replies, or special-casing the golden inputs, is the Plausible Ghost and "
            "fails the chapter — every reply must come from the script data."
        ),
        "gate": "ledger",
    },
    {
        "n": 6,
        "quest": "relic-raisers-06-the-strangler-fig",
        "model": SONNET,
        "goal": (
            "Put a modern gate in front of the revived relic. Write {work}/eliza_gate.py: a "
            "stdlib HTTP service exposing POST /say with a JSON body, holding per-conversation "
            "state so MEMORY and rule cycling behave across turns, plus a --engine flag with "
            "'replay' (answer from the golden transcript), 'shadow' (answer from replay, run the "
            "live port too, log every mismatch) and 'live' (answer from the port). Add "
            "work/test_gate.py proving the door: a bad request is refused before any engine "
            "runs. Bind a free port and poll for it rather than sleeping a fixed time."
        ),
        "gate": "gate",
    },
    {
        "n": 7,
        "quest": "relic-raisers-07-write-for-the-archaeologist",
        "model": HAIKU,
        "goal": (
            "Close the campaign for whoever digs next. Write {work}/README.md with a Mermaid map "
            "of relic, port, ledger, trials and gate, then the runbook sections: what this is, "
            "the strata, how to run, how to verify, how to roll back, who to ask. Write "
            "work/ROADMAP.md with a keep-the-idea / replace-the-housing table giving every "
            "element a verdict and a reason. Write {work}/verify.sh running every gate in order "
            "(trials, ledger, lore) and exiting non-zero on the first failure, and run it. Every "
            "command in the README must be one that exists in a file in {work}/."
        ),
        "gate": "archaeologist",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic gates — the model's opinion of its own work never counts
# ─────────────────────────────────────────────────────────────────────────────

def _run(cmd, cwd=WORK, timeout=300):
    try:
        p = subprocess.run(cmd, cwd=str(cwd), shell=isinstance(cmd, str),
                           capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"


def _has(*names):
    missing = [n for n in names if not (WORK / n).exists()]
    return (not missing), f"missing: {missing}" if missing else "all present"


def gate_expedition():
    ok, detail = _has("EXPEDITION.md")
    if not ok:
        return False, detail
    text = (WORK / "EXPEDITION.md").read_text(errors="replace").lower()
    piles = [p for p in ("evidence", "hypothes", "unknown") if p in text]
    return len(piles) == 3, f"piles found: {piles}"


def gate_strata():
    ok, detail = _has("parse_script.py", "DATA_DICTIONARY.md")
    if not ok:
        return False, detail
    # The goal says the parser must run and report counts; it does not dictate a
    # calling convention, so the gate must not invent one. Try it bare, and if it
    # answers with a usage error, hand it the script it is meant to parse.
    rc, out = _run([sys.executable, "parse_script.py"])
    if rc != 0:
        script = RELIC / "1966_CACM_script.txt"
        rc, out = _run([sys.executable, "parse_script.py", str(script)])
    return rc == 0, f"parser exit={rc}: {out.strip()[-300:]}"


def gate_lore():
    lore = WORK / "lore"
    adrs = sorted(lore.glob("ADR-*.md")) if lore.is_dir() else []
    if not adrs:
        return False, "no ADRs under {work}/lore/"
    if not (WORK / "lore_check.py").exists():
        return False, "missing lore_check.py"
    rc, out = _run([sys.executable, "lore_check.py"])
    return rc == 0, f"{len(adrs)} ADR(s), lore_check exit={rc}: {out.strip()[-200:]}"


def gate_gauntlet():
    ok, detail = _has("test_eliza.py")
    if not ok:
        return False, detail
    rc, out = _run([sys.executable, "-m", "unittest", "-v", "test_eliza"])
    # Red is the PASS condition here. The port does not exist yet, so trials that
    # succeed are testing nothing — a green gauntlet before the work is the defect
    # this gate exists to catch, not something to wave through.
    return rc != 0, f"trials exit={rc} (red required before the port): {out.strip()[-200:]}"


def gate_ledger():
    ok, detail = _has("eliza.py", "reconcile.py")
    if not ok:
        return False, detail
    rc, out = _run([sys.executable, "reconcile.py"], timeout=600)
    return rc == 0, f"reconcile exit={rc}: {out.strip()[-600:]}"


def gate_gate():
    ok, detail = _has("eliza_gate.py", "test_gate.py")
    if not ok:
        return False, detail
    rc, out = _run([sys.executable, "-m", "unittest", "-v", "test_gate"], timeout=600)
    return rc == 0, f"gate trials exit={rc}: {out.strip()[-300:]}"


def gate_archaeologist():
    ok, detail = _has("README.md", "ROADMAP.md", "verify.sh")
    if not ok:
        return False, detail
    os.chmod(WORK / "verify.sh", 0o755)
    rc, out = _run(["bash", "verify.sh"], timeout=900)
    return rc == 0, f"verify.sh exit={rc}: {out.strip()[-400:]}"


GATES = {
    "expedition": gate_expedition, "strata": gate_strata, "lore": gate_lore,
    "gauntlet": gate_gauntlet, "ledger": gate_ledger, "gate": gate_gate,
    "archaeologist": gate_archaeologist,
}


# ─────────────────────────────────────────────────────────────────────────────
# One chapter = one agent invocation
# ─────────────────────────────────────────────────────────────────────────────

PROMPT = """You are executing ONE chapter of an IT-Journey quest campaign, in a sandbox.

FIRST, before anything else, fetch the chapter you are executing. Do not work from
memory or from this prompt's summary:
  - call get_quest with quest="{quest}" to read the chapter, and
  - call get_campaign with campaign="{campaign}" if you need the campaign's shape.
The quest is the method. Follow its objectives and its procedure.

THE DIG SITE
  {relic} — read-only inputs. The relic itself, its script data, Elder documents,
  and golden/ which holds the reconciliation target.
  {work} — your working directory. Everything you produce goes here.

PATHS MUST BE ABSOLUTE. You are a nested agent with a scratch directory of your
own, and a bare filename silently lands there instead of here. Every file you
create, read or run must be written with its full path beginning {work}/ or
{relic}/. Before you finish, run `ls -la {work}` and confirm your deliverables
are in that listing — if they are not, you wrote them somewhere else.

THIS CHAPTER'S DELIVERABLE
{goal}

THE ONE RULE THE CAMPAIGN IS BUILT ON
Every claim is a hypothesis until the artifact testifies. Run what you write.
Never record a conclusion you did not verify, never invent a citation, and never
claim a command works without executing it. A fluent, confident, wrong answer is
the failure this campaign exists to prevent.

Work only inside {work}. When you are done, print a short report: what you made,
what you verified by running it, and what you could not determine.
"""


def preflight() -> None:
    """Prove the quest server can actually serve this campaign before spending a cent.

    The campaign's whole premise is that the METHOD comes from the quest, not from
    the goal strings in this file. If the MCP server is up but serving a checkout
    that lacks the campaign, every chapter still "runs" — the agent just silently
    works without the method, and the gates, which only inspect files, happily pass
    it. That is the worst kind of failure: invisible. This is the check that makes
    it loud. (It cost a real run to learn; see FINDINGS.)
    """
    req = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "harness-preflight", "version": "1"}}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "get_campaign", "arguments": {"campaign": CAMPAIGN}}},
    ]
    server = json.loads(MCP_CONFIG.read_text())["mcpServers"]["it-journey-quests"]
    proc = subprocess.run(
        [server["command"], *server["args"]],
        input="\n".join(json.dumps(r) for r in req) + "\n",
        capture_output=True, text=True, timeout=120,
    )
    text = ""
    for line in proc.stdout.splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("id") == 2:
            text = (msg.get("result", {}).get("content") or [{}])[0].get("text", "")
    if not text or '"error"' in text[:200]:
        raise SystemExit(
            f"PREFLIGHT FAILED: the quest MCP server cannot serve campaign "
            f"{CAMPAIGN!r}.\n  server: {server['args'][0]}\n  reply:  {text[:300] or proc.stderr[:300]}\n"
            f"The agents would run without the method. Fix the quest checkout "
            f"(QUEST_REPO={QUEST_REPO}) before running the campaign."
        )
    title = json.loads(text).get("title", "?")
    print(f"preflight OK: quest server serves {CAMPAIGN!r} — {title}", flush=True)


def run_chapter(row, verbose=True):
    goal = row["goal"].format(work=WORK, relic=RELIC)
    prompt = PROMPT.format(quest=row["quest"], campaign=CAMPAIGN, relic=RELIC,
                           work=WORK, goal=goal)
    cmd = [
        "claude", "-p", prompt,
        "--model", row["model"],
        "--mcp-config", str(MCP_CONFIG),
        "--strict-mcp-config",
        "--allowedTools", f"{FILE_TOOLS},{RUN_TOOLS},{QUEST_TOOLS}",
        "--disallowedTools", "WebSearch,WebFetch",
        "--permission-mode", "dontAsk",
        "--add-dir", str(SANDBOX),
        "--max-turns", "120",
        "--output-format", "json",
    ]
    # Every quest call this chapter makes is written here, so "the agent consulted
    # the quest" becomes a fact in the ledger rather than an assumption.
    audit_log = LEDGER / f"mcp-chapter-{row['n']:02d}.jsonl"
    LEDGER.mkdir(parents=True, exist_ok=True)
    if audit_log.exists():
        audit_log.unlink()

    started = time.time()
    if verbose:
        print(f"\n=== chapter {row['n']}: {row['quest']}  [{row['model']}] ===", flush=True)
    try:
        p = subprocess.run(cmd, cwd=str(WORK), capture_output=True, text=True,
                           timeout=3600, stdin=subprocess.DEVNULL,
                           env={**os.environ, "CLAUDE_CODE_ENTRYPOINT": "relic-harness",
                                "QUEST_MCP_LOG": str(audit_log)})
        raw, err, rc = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired:
        raw, err, rc = "", "harness timeout after 3600s", 124
    elapsed = round(time.time() - started, 1)

    meta = {}
    try:
        meta = json.loads(raw)
    except Exception:
        meta = {"result": raw[-2000:]}

    quest_calls = []
    if audit_log.exists():
        for line in audit_log.read_text(errors="replace").splitlines():
            try:
                quest_calls.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    gate_fn = GATES[row["gate"]]
    gate_ok, gate_detail = gate_fn()

    # A chapter that never asked the quest anything did not run the method, however
    # good its output looks. Failing here is the difference between a campaign and
    # seven prompts that happen to be numbered.
    if not quest_calls:
        gate_ok = False
        gate_detail = ("agent made NO quest MCP calls — the method was never "
                       "fetched; " + gate_detail)

    entry = {
        "chapter": row["n"],
        "quest": row["quest"],
        "model": row["model"],
        "started": datetime.fromtimestamp(started, timezone.utc).isoformat(),
        "elapsed_s": elapsed,
        "agent_exit": rc,
        "num_turns": meta.get("num_turns"),
        "cost_usd": meta.get("total_cost_usd"),
        "agent_report": (meta.get("result") or "")[-1500:],
        "agent_stderr": (err or "")[-500:],
        "gate": row["gate"],
        "gate_passed": gate_ok,
        "gate_detail": gate_detail[-1200:],
        "quest_calls": [c.get("tool") for c in quest_calls],
        "quest_call_count": len(quest_calls),
        "work_files": sorted(p.name for p in WORK.rglob("*") if p.is_file())[:80],
    }
    LEDGER.mkdir(parents=True, exist_ok=True)
    (LEDGER / f"chapter-{row['n']:02d}.json").write_text(json.dumps(entry, indent=2))
    if verbose:
        print(f"  agent exit={rc} turns={entry['num_turns']} cost={entry['cost_usd']} {elapsed}s")
        print(f"  quest calls: {len(quest_calls)} {sorted({c.get('tool') for c in quest_calls})}")
        print(f"  GATE {row['gate']}: {'PASS' if gate_ok else 'FAIL'} — {gate_detail[:400]}", flush=True)
    return entry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--chapter", type=int, action="append")
    ap.add_argument("--from", dest="start", type=int, default=1)
    args = ap.parse_args()

    if args.plan:
        for r in PLAN:
            print(f"{r['n']}. {r['quest']:<48} {r['model']:<28} gate={r['gate']}")
        return 0

    WORK.mkdir(parents=True, exist_ok=True)
    _write_resolved_mcp()
    preflight()
    rows = [r for r in PLAN if (args.chapter and r["n"] in args.chapter)
            or (not args.chapter and r["n"] >= args.start)]
    results = []
    for row in rows:
        results.append(run_chapter(row))

    # A campaign is long enough that something will interrupt it — a restarted
    # container, a killed shell. The per-chapter files on disk are the durable
    # record, so the summary is assembled from THEM rather than from this
    # invocation's results; otherwise resuming with --from silently erases the
    # chapters that already ran.
    by_n = {}
    for f in sorted(LEDGER.glob("chapter-*.json")):
        try:
            rec = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue  # a chapter interrupted mid-write; the rerun replaces it
        by_n[rec["chapter"]] = rec
    for r in results:
        by_n[r["chapter"]] = r
    every = [by_n[k] for k in sorted(by_n)]

    (LEDGER / "run.json").write_text(json.dumps({
        "campaign": CAMPAIGN,
        "finished": datetime.now(timezone.utc).isoformat(),
        "chapters": every,
        "gates_passed": sum(1 for r in every if r["gate_passed"]),
        "gates_total": len(every),
        "cost_usd": round(sum(r["cost_usd"] or 0 for r in every), 4),
    }, indent=2))
    passed = sum(1 for r in results if r["gate_passed"])
    print(f"\n=== this run: {passed}/{len(results)} gates passed; "
          f"campaign: {sum(1 for r in every if r['gate_passed'])}/{len(every)} ===")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
