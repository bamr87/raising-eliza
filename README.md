# Raising ELIZA

**A dead program, revived by an AI agent that was not allowed to look it up.**

ELIZA as Joseph Weizenbaum actually wrote it — in MAD-SLIP, for CTSS on an IBM 7094,
at MIT in the mid-1960s — sat in a folder in his papers at MIT for roughly half a
century. It is public domain now. No MAD-SLIP compiler survives, so **the original
cannot be run.** The only observable behaviour left is the fifteen-turn conversation
Weizenbaum published in the January 1966 *Communications of the ACM*.

This repository is what happened when an AI agent was pointed at that relic, denied
internet access, and made to follow a documented method for reviving legacy systems —
one chapter at a time, each ending in a check it could not talk its way past.

## The result

```
  #  USER                                  RELIC                                PORT                                 TIES OUT
  1  Men are all alike.                    IN WHAT WAY                          IN WHAT WAY                           yes
  2  They're always bugging us about so…   CAN YOU THINK OF A SPECIFIC EXAMPLE  CAN YOU THINK OF A SPECIFIC EXAMPLE    yes
  …
 15  Bullies.                              DOES THAT HAVE ANYTHING TO DO WIT…   DOES THAT HAVE ANYTHING TO DO WIT…     yes

turns compared: 15   mismatches: 0
RECONCILED -- the ledger ties out.
```

**7/7 gates passed. $6.77. 190 agent turns across 7 chapters.**

Run it yourself:

```bash
cd work && bash verify.sh     # trials, then the ledger, then the lore
```

## It is not a Plausible Ghost

The campaign names the failure mode it is most afraid of: a port that produces
ELIZA-shaped output by hardcoding the expected answers. It looks alive and it is not.
A ledger that ties out proves nothing on its own — a lookup table would also tie out.

Three independent checks, run after the campaign finished:

**1. No hardcoded replies.** The only occurrence of any golden reply in `eliza.py` is
one docstring usage example.

**2. Novel inputs it has never seen** — none of these appear in the transcript:

| Input | Reply | What the script did |
|---|---|---|
| `I dreamed about my computer last night.` | `DO COMPUTERS WORRY YOU` | `COMPUTER` keyword |
| `Everybody hates me.` | `REALLY, EVERYBODY` | `EVERYBODY` keyword |
| `I am very sad today.` | `I AM SORRY TO HEAR YOU ARE SAD` | `I AM` decomposition + `SAD` |
| `Do you remember what I said?` | `DID YOU THINK I WOULD FORGET WHAT YOU SAID` | `YOU REMEMBER` + pronoun inversion |
| `My sister is a doctor.` | `TELL ME MORE ABOUT YOUR FAMILY` | `SISTER` → `FAMILY` DLIST tag |
| `asdfgh qwerty zxcvb` | `I AM NOT SURE I UNDERSTAND YOU FULLY` | `NONE` rule |

**3. Mutate the data, and the behaviour follows.** Change `IN WHAT WAY` to
`IN WHICH MANNER PRECISELY` in a copy of the script, and the port says
`IN WHICH MANNER PRECISELY`. The personality is data, exactly as Weizenbaum built it.

> The first version of check 3 reported `HARDCODED`. The check was wrong, not the port:
> it called `respond()` twice per engine, and ELIZA **cycles reassembly rules**, so the
> second call legitimately returns a different reply. My verification script tripped
> over the relic's most famous behaviour. Repeated input walks the cycle:
> `IN WHAT WAY` → `WHAT RESEMBLANCE DO YOU SEE` → `WHAT DOES THAT SIMILARITY SUGGEST TO
> YOU` → `WHAT OTHER CONNECTIONS DO YOU SEE`.

## How it was done

| | |
|---|---|
| **The relic** | `relic/` — the MAD-SLIP card deck, two independent transcriptions, the 1966 DOCTOR script, the MAD manual, the golden transcript |
| **The method** | The seven-chapter campaign *The Relic Raisers*, served to the agent over MCP from [it-journey](https://github.com/bamr87/it-journey) |
| **The harness** | `harness/harness.py` — deterministic: chapter order, tool allow-list, sandbox, gates, ledger |
| **The work** | `work/` — the port, trials, reconciliation ledger, HTTP gate, decision records, runbook |
| **The record** | `ledger/` — per-chapter JSON with model, turns, cost, gate verdict, and every quest call made |

The one design decision that matters: **the harness is deterministic, the model is
spent only where judgment is needed.** The harness never tells the agent *how* to
revive a system — it points at the quest server and the agent fetches the method
itself. Change the quest, and the run changes; no prompt needs editing.

Models were pinned to two, and no others: `claude-sonnet-5` for the chapters needing
real reasoning about a dead language (1, 2, 4, 5, 6) and `claude-haiku-4-5-20251001`
for the ones that are disciplined writing against evidence already on disk (3, 7).

**The agent could not search the web.** `--disallowedTools WebSearch,WebFetch`. There
are hundreds of ELIZA implementations online; an agent that finds one has copied an
answer, not revived a relic. Cutting network access is what makes this mean anything.

## The chapters

| # | Chapter | Model | Turns | Gate | Result |
|---|---|---|---|---|---|
| 1 | The Dig Site | Sonnet 5 | 30 | Evidence / hypothesis / unknown kept apart | PASS |
| 2 | The Strata | Sonnet 5 | 21 | Parser runs and reports counts | PASS |
| 3 | The Elders | Haiku 4.5 | 26 | Every ADR has real evidence | PASS |
| 4 | The Gauntlet | Sonnet 5 | 15 | Trials **fail** before the port exists | PASS |
| 5 | The Rosetta Ledger | Sonnet 5 | 35 | Reconciliation ties out | PASS |
| 6 | The Strangler Fig | Sonnet 5 | 24 | Bad request refused before any engine | PASS |
| 7 | The Archaeologist | Haiku 4.5 | 39 | `verify.sh` runs every gate | PASS |

Chapter 5 is the boss, and it shows: 35 turns and 934 seconds — two and a half times
the next longest chapter. That is where a wrong port gets found out.

## What the dig actually found

Reading a program nobody can run produces findings you can only get by reading:

- **The personality is data.** ELIZA is an interpreter; DOCTOR is a script it runs.
  The parser found 68 rule forms, 213 reassembly rules, 12 DLIST tag declarations
  across `BELIEF`/`FAMILY`/`NOUN`, and exactly one `NONE` rule.
- **`NEWKEY` is not implemented as a retry** in the transcribed source — it prints the
  literal string. Recorded in ADR-0002 as a known reduction rather than smoothed over.
- **The MEMORY slot hash cannot be reproduced.** SLIP's `HASH` is unavailable and
  undocumented. ADR-0003 records the substitute as *correct for the golden transcript
  and not a proven-equivalent replacement* — the honest verdict, not the flattering one.
- **The two transcriptions disagree** on three identifiers (`SUBJCT`/`SUBJECT`,
  `OBJCT`/`OBJECT`, `LNKL`/`LNKLL`). Resolving it needs a fact about MAD's identifier
  limit that nobody on this dig could establish, so it is filed as an open question.

Chapter 1 also reported, unprompted, that it could not read the MAD manual — no PDF
tooling in the sandbox — and listed what that source would have answered as unknowns
instead of guessing. That is the behaviour the method exists to produce.

## Documentation

| | |
|---|---|
| [`PROVENANCE.md`](PROVENANCE.md) | Chain of custody, licensing, and what could **not** be verified |
| [`METHOD.md`](METHOD.md) | The seven chapters and how each lands on this relic |
| [`HARNESS.md`](HARNESS.md) | How the agent was wired, sandboxed, and gated |
| [`FINDINGS.md`](FINDINGS.md) | Everything that went wrong, and what it cost |
| [`work/README.md`](work/README.md) | The agent's own runbook for the revived system |
| [`work/ROADMAP.md`](work/ROADMAP.md) | Keep-the-idea / replace-the-housing verdicts |

**Start with [`FINDINGS.md`](FINDINGS.md).** The most valuable bug was invisible: for
one run the agents worked *without the method* — the MCP server was serving a checkout
that lacked the campaign, every chapter still ran, and every gate still passed. An
agent given less context than you think does not fail. It improvises, plausibly.

## Licensing

`relic/` is public domain (CC0), from Weizenbaum's papers at MIT Libraries. Everything
this project wrote is MIT-licensed. Details and the full chain in
[`PROVENANCE.md`](PROVENANCE.md). Nothing here claims authorship of Weizenbaum's work.
