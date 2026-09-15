# The harness

How an AI agent was wired to a quest and pointed at a dead program.

## The one design decision that matters

**The harness is deterministic. The model is spent only where judgment is needed.**

Everything that can be a script is a script: the chapter order, the tool allow-list,
the sandbox boundary, the gates, the ledger. The model gets exactly one job per
chapter — read a dead language, or write a port — and a deterministic gate decides
whether it succeeded. The gate's verdict, not the model's own report, is what the
ledger records.

This matters because a model asked "did you do it?" will usually say yes. Chapter 5's
agent could claim the ledger ties out; `reconcile.py` exiting non-zero says otherwise,
and the non-zero is what gets written down.

## The method lives in the quest, not in the prompts

The harness never tells the agent *how* to revive a system. It tells the agent which
chapter it is executing and points it at an MCP server that serves the quest. The
agent fetches the method itself.

```
harness.py ──spawns──> claude -p ──MCP──> it-journey-quests ──reads──> the quest repo
   │                       │
   │ owns: order,          │ owns: judgment —
   │ tools, sandbox,       │ reading MAD-SLIP,
   │ gates, ledger         │ writing the port
   ▼                       ▼
ledger/chapter-NN.json   work/*.py
```

Change the quest and the run changes. No prompt in `harness.py` needs editing. That is
the difference between a harness and a pile of prompts: the method is versioned
content, the harness is plumbing.

## Models

Two, pinned, and no others:

| Model | Chapters | Why |
|---|---|---|
| `claude-sonnet-5` | 1, 2, 4, 5, 6 | Reasoning about a dead language, designing the port, building the ledger and the gate |
| `claude-haiku-4-5-20251001` | 3, 7 | Disciplined writing against evidence already on disk — decision records and the runbook |

Chapter 3 writes decision records from files chapter 1 already read, and chapter 7
writes a runbook from files chapters 2–6 already produced. Neither needs the larger
model, and the split is a real cost decision, not decoration.

## The sandbox

Each chapter is one `claude -p` invocation:

```
claude -p <goal> --model <pinned>
  --mcp-config harness/mcp.resolved.json --strict-mcp-config
  --allowedTools Read,Write,Edit,Glob,Grep,Bash,mcp__it-journey-quests__*
  --disallowedTools WebSearch,WebFetch
  --permission-mode dontAsk
  --add-dir <sandbox> --max-turns 120
  --output-format json
```

- `--strict-mcp-config` means the run sees the quest server and nothing else — no
  ambient MCP servers leak in from the developer's own configuration.
- `--disallowedTools WebSearch,WebFetch` is the important one. **The agent may not
  look ELIZA up.** There are hundreds of ELIZA implementations on the public web, and
  an agent that finds one has not revived a relic, it has copied an answer. Cutting
  network access is what makes the result mean anything.
- `--add-dir` scopes writes to the sandbox.
- `--output-format json` gives the harness turn counts and cost per chapter, which is
  how the ledger can report what the campaign actually spent.

### Absolute paths, always

An early probe exposed a quiet failure: a nested agent told to write `probe.txt`
reported success with a real turn count and cost, and the file landed in *its own*
scratchpad rather than the sandbox. Every goal now names absolute paths, and the
prompt carries the rule explicitly — a bare filename silently lands somewhere else.

## The gates

One deterministic check per chapter. A gate is a Python function returning
`(passed, detail)`; the detail goes in the ledger verbatim.

| Chapter | Gate | What it actually proves |
|---|---|---|
| 1 The dig site | `expedition` | `EXPEDITION.md` separates evidence, hypotheses and unknowns |
| 2 The strata | `strata` | `parse_script.py` runs and reports counts |
| 3 The elders | `lore` | ADRs exist and `lore_check.py` fails any with an empty Evidence section |
| 4 The gauntlet | `gauntlet` | The trials are **red** — see below |
| 5 The Rosetta ledger | `ledger` | `reconcile.py` exits zero: the port matches all fifteen published turns |
| 6 The strangler fig | `gate` | The service refuses a bad request before any engine runs |
| 7 The archaeologist | `archaeologist` | `verify.sh` runs every gate in order and exits zero |

Chapter 4's gate is the subtle one. Its purpose is to prove the trials *fail* before
the port exists, because trials that pass against nothing are testing nothing. The
first version of this gate returned `True` unconditionally — it would have waved
through exactly the defect it existed to catch. See `FINDINGS.md`.

## The ledger

Per-chapter JSON on disk is the durable record: model, elapsed time, turns, cost,
agent exit code, gate verdict, gate detail, and the files that appeared in `work/`.
`run.json` is assembled from those files rather than from the current invocation, so
resuming after an interruption does not erase the chapters that already ran. That was
also a bug, found the way such bugs usually are — the container restarted mid-campaign.

## Running it yourself

The harness needs a checkout of the quest repository, because that is where the method
lives. `QUEST_REPO` points at it (default `/home/user/it-journey`).

```bash
git clone https://github.com/bamr87/it-journey.git
export QUEST_REPO="$PWD/it-journey"

# Confirm the server can serve the campaign BEFORE running anything.
python3 "$QUEST_REPO/scripts/quest/mcp_server.py" --self-test
cd harness && python3 harness.py --plan     # the chapter plan, no agent spawned
python3 harness.py                          # the whole campaign
python3 harness.py --chapter 5              # just the boss
```

`harness.py` runs `preflight()` first and refuses to start if `get_campaign` does not
resolve, so a checkout missing the campaign fails loudly at the start instead of
quietly producing seven chapters of work done without the method.

The MCP server itself is on it-journey's `main`. The *campaign content* — the seven
chapters this run executed — is still open as a pull request at the time of writing;
until it lands on `main`, preflight will correctly refuse to start, and the fix is to
check out the branch carrying it. That refusal is the feature working.

Re-running does not reproduce this run exactly. The gates are deterministic; the agent
is not. What should reproduce is the *shape*: red trials in chapter 4, a ledger that
ties out in chapter 5, and a `work/` tree that passes `verify.sh`. If chapter 5's
ledger does not tie out, that is the method working — it caught a port that did not.
