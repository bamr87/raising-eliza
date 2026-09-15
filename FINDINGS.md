# Findings

Everything that went wrong, and what it cost. These are the useful part of the
exercise — a run where nothing breaks teaches nothing about running agents.

## 1. The silent one: agents ran without the method

**The worst bug of the project, and it was invisible.**

The quest content and the MCP server lived on two different branches of the quest
repository. After a container restart the checkout came up on the branch holding the
*server* but not the *campaign*. The MCP server started fine. It answered fine. It
answered `no campaign matches 'relic-raisers'`.

The chapter still ran. The agent still worked from the goal string in the harness. The
gates still inspected files, found them, and passed. Nothing anywhere said the method
had gone missing — the exact premise of the whole campaign — and the run would have
completed looking entirely successful.

**Why the gates could not catch it:** every gate asked "does the output look right?"
None asked "did the agent have the input?"

**The fix, in two parts:**

1. A `preflight()` that calls `get_campaign` before spending a cent and refuses to
   start if the campaign does not resolve. Verified in both directions: it passes on a
   good checkout and fails on a checkout lacking the campaign, reproduced with a git
   worktree of the server-only branch.
2. An audit log. `QUEST_MCP_LOG` makes the MCP server append one line per served call;
   the harness points it at a per-chapter file and **fails any chapter that made zero
   quest calls**. "The agent consulted the quest" is now a fact in the ledger with the
   tool names attached, not an assumption.

The general lesson is bigger than this project: *an agent given less context than you
think does not fail — it improvises, plausibly.* If context arrives over a channel that
can degrade, something has to assert the channel is live, and something has to record
that it was used. Neither is the model's job.

The whole campaign was re-run from chapter 1 afterwards, because the earlier chapters
could not be *proven* to have had the method. The first partial run is kept in
`archive-run-1/` rather than deleted.

## 2. A gate that would have passed the defect it existed to catch

Chapter 4's gate exists to prove the trials are **red** before the port is written,
because trials that pass against a port that does not exist are testing nothing.

```python
# before
return True, f"trials exit={rc} (red expected before the port): ..."
```

It returned `True` unconditionally. A green gauntlet — the precise failure the chapter
is designed to prevent — would have sailed through.

```python
# after
return rc != 0, f"trials exit={rc} (red required before the port): ..."
```

Found by reading my own gates back rather than trusting that they did what their names
said. Worth doing for every gate you write: *what output would make this gate wrong?*

## 3. A gate asserting an interface nobody specified

Chapter 2's gate ran `python3 parse_script.py` with no arguments. The agent had written
a parser taking the script path as an argument — a perfectly reasonable reading of a
goal that never specified a calling convention. Exit code 2, argparse usage error,
`GATE strata: FAIL`.

The parser was correct. Run properly it reports 68 rule forms, 213 reassembly rules,
12 DLIST tag declarations across `BELIEF`/`FAMILY`/`NOUN`, and exactly one `NONE` rule.
The gate was wrong, not the work.

Fixed to try bare, then hand the parser the script it is meant to parse. The ledger
entry keeps **both** verdicts — `gate_passed_original_run` alongside the corrected one,
with a note explaining the re-run and stating that the agent's artifact was not
modified or regenerated. A ledger you silently correct is not a ledger.

## 4. Resuming a campaign erased the campaign

`run.json` was assembled from the current invocation's results. Resume with `--from 3`
and chapters 1–2 vanish from the summary — while their per-chapter files sat on disk,
intact, ignored.

Found the way these things are always found: the container restarted mid-run. Now the
summary is assembled from the per-chapter files on disk, with malformed ones (a chapter
interrupted mid-write) skipped rather than fatal.

Any harness expected to run for an hour will be interrupted. Resumability is not a
nicety, and the durable record has to be the thing on disk, not the thing in memory.

## 5. The MCP server answered a guess with a riddle

Calling `get_campaign` with `{"slug": "relic-raisers"}` instead of
`{"campaign": "relic-raisers"}` returned:

```
no campaign matches None
```

The schema declared `campaign` required; the server never enforced it and passed `None`
through to a lookup. An agent that guesses a parameter name — which I did, as the first
client of my own server — gets a semantic error about the wrong thing entirely.

Now:

```json
{"error": "missing required argument(s): campaign", "expected": ["campaign"]}
```

Tool errors are read by something that cannot ask you what you meant. Say what is
missing and what was expected.

## 6. Agents write where you didn't look

An early probe told a nested agent to write `probe.txt`. It reported success with a
real turn count and cost. The file was in the agent's *own* scratchpad, not the
sandbox.

Nothing lied. The report was accurate about a file nobody wanted. Every goal now names
absolute paths, and the prompt carries the rule: a bare filename silently lands
somewhere else.

## 7. Root cannot bypass permissions

`--permission-mode bypassPermissions` maps to `--dangerously-skip-permissions`, which
refuses to run with root privileges. Switched to `dontAsk`, which is the right level
anyway: the sandbox boundary is `--add-dir` and the tool allow-list, not the permission
mode.

## 8. The relic's own missing tool

Chapter 1 reported, honestly, that it could not read `MAD_Primer.pdf` — no
`pdftoppm` in the sandbox — and listed the two questions that source would have
answered as unknowns rather than guessing at them.

That is the behaviour the method is trying to produce, and it was worth more than a
silent guess would have been. Installing `poppler-utils` closed the gap for later
chapters.
