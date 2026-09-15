# The method

The seven chapters of *The Relic Raisers*, what each one demands, and how that maps
onto the ELIZA dig.

The campaign is content in the [it-journey](https://github.com/bamr87/it-journey)
repository, served to the agent over MCP. The harness does not restate it. The agent
fetches each chapter and executes it.

| # | Level | Chapter | The demand |
|---|---|---|---|
| 1 | `0011` | The Dig Site: Unearth the Relic and Name What You Do Not Know | Separate evidence from hypothesis from unknown |
| 2 | `0110` | The Strata: Read the Copybook, Then Let the Data Testify | Decode the data format; make the data testify |
| 3 | `1111` | The Elders: Recover the Reasons Before They Retire | Recover *why*, with evidence, before the people are gone |
| 4 | `0101` | The Gauntlet of Trials: Pin the Relic Before You Touch It | Pin behaviour in tests **before** changing anything |
| 5 | `1100` | The Rosetta Ledger: Translate the Relic and Prove It Ties Out | Port it, and prove equivalence line for line |
| 6 | `0111` | The Strangler Fig: Put a Modern Gate in Front of the Relic | Modern gate, shadow mode, rollback |
| 7 | `1110` | Write for the Archaeologist: Leave the Lore Where the Next One Digs | Map, runbook, roadmap for whoever digs next |

## What the campaign was originally written for

A COBOL accounts-receivable aging program: a copybook, packed decimal fields, a Y2K
pivot window, an executable you can still compile and run.

ELIZA is a harder case in one specific way, and that is why it was chosen. **You cannot
run the relic.** No MAD-SLIP compiler survives. The COBOL version of chapter 1 says
"compile it and run it"; here there is nothing to run, and every later chapter has to
work from reading alone, with a single fifteen-turn transcript as the only surviving
observable behaviour.

That is not a weakness of the exercise. It is the condition most real legacy work is
heading toward: the binary runs but nobody can rebuild it, or the environment that
compiled it is gone. The method has to survive the loss of the oracle.

## How each chapter lands on this relic

**1 — The dig site.** Read `MAD-SLIP_transcription.txt` (the card deck, sequence
numbers in columns 73–80), the annotated second transcription, and the MAD manual.
Write `EXPEDITION.md` with three piles kept apart. The rule that does the work: *an
inference written down as a fact is how a port goes wrong six weeks later.*

**2 — The strata.** ELIZA's "copybook" is the DOCTOR script — the rule data from the
1966 CACM appendix. Parse it into structured rules; document every construct with
evidence. This chapter is where the central insight of ELIZA surfaces: the program is
an interpreter, and the personality is *data*.

**3 — The elders.** Weizenbaum died in 2008. The elders are unreachable, so the lore
has to be recovered from what they left: the code, the translation, the annotations.
Decision records, five sections each, and a `lore_check.py` that fails any ADR whose
Evidence section is empty. The check exists because an ADR with no evidence is a
rumour with a template.

**4 — The gauntlet.** Trials that assert the port reproduces the published conversation
turn by turn — written *before* the port, and **required to fail**. Trials that pass
against nothing are testing nothing.

**5 — The Rosetta ledger.** The boss. Port the relic, driven by the 1966 script as
data, then reconcile: run the port over the transcript's USER lines and compare each
reply to the published ELIZA line. Exit non-zero on any mismatch.

> The named failure mode here is the **Plausible Ghost**: a port that produces
> ELIZA-shaped output by hardcoding or special-casing the golden inputs. It looks
> alive and it is not. The ledger is what tells them apart, which is why the ledger,
> not the output, is the deliverable.

**6 — The strangler fig.** A modern HTTP gate in front of the revived relic, with three
engines — `replay` (answer from the transcript), `shadow` (answer from replay, run the
port too, log every mismatch), `live` (answer from the port). Shadow mode is how you
find out whether a port is right on traffic you did not choose.

**7 — Write for the archaeologist.** The next person to dig here is the audience. Map,
runbook, roadmap, and a `verify.sh` that runs every gate in order — with the rule that
every command in the README must exist in a file.

## The part that is not about ELIZA

Chapter 5's `reconcile.py` is the shape of the whole method. Before you are allowed to
say a translation is correct, you build the thing that would *catch you* if it were
not, and you make its verdict machine-readable. Everything else — the evidence piles,
the empty-evidence check, the red gauntlet, shadow mode — is that same move applied
earlier or later.

An AI agent will produce confident, plausible, well-structured output about a system
it has misread. So will a contractor. The method does not depend on trusting either.
