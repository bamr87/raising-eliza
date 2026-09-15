# ADR-0005: When MAD-SLIP becomes available, the relic and port must be revalidated before the port can be trusted on new inputs

## Status

Deferred, review by 2050-01-01

## Context

This port (eliza.py) has been validated against one golden transcript of 15 exchanges, showing zero mismatches. Validation is limited by the fact that only the transcript survives; the original MAD-SLIP source cannot run because no MAD-SLIP compiler exists at this dig site.

Two parts of the port are reconstructions, not recovered facts:
1. ADR-0003: The MEMORY mechanism uses a deterministic backward cycle, not the original SLIP HASH algorithm (which is undocumented and unavailable).
2. ADR-0002: NEWKEY is not implemented as a retry; it prints the literal string (verified in the transcribed code, not exercised by the golden transcript).

These reconstructions are correct *for the golden transcript* but may be wrong *for inputs not in the transcript*. If a MAD-SLIP compiler becomes available and Weizenbaum's original source can be run, the port's behavior on new inputs must be checked against the relic.

## Decision

The port is accepted for use in production *on inputs similar to the 15-turn golden conversation*. It is **not** accepted for arbitrary new inputs until a MAD-SLIP compiler is available and a validation runs the original relic against new inputs side-by-side with the port.

When a MAD-SLIP compiler becomes available, the relic should be run on:
1. The golden transcript (to validate the transcript-and-port match still holds).
2. A new test corpus of at least 100 turns of conversation, with:
   - Multiple NEWKEY rule exercises (to validate ADR-0002's reconstruction)
   - Multiple different inputs that trigger MY/MEMORY (to validate ADR-0003's reconstruction)
   - Edge cases (repeated keywords, clause delimiters in unusual positions, etc.)

If the relic produces the same output as the port on this corpus, ADR-0003 and ADR-0002 can be promoted from "reconstruction" to "verified". If it produces different output, a new ADR must record the differences and decide: does the port need fixing, or was the reconstruction correct for our use case and the relic was wrong?

## Evidence

- `eliza.py:50-58`: The port's docstring documents MEMORY as a reconstruction, not a recovered fact.
- `ADR-0002`: NEWKEY is not exercised by the golden transcript, so its behavior (printing the literal string) is not validated.
- `reconcile.py` output: Zero mismatches on the 15-turn golden transcript; this does not imply zero mismatches on arbitrary input.
- `test_eliza.py`: All 19 trials pass (including the 15 turn trials), but trials cover only what is in the golden transcript.

## Consequences

- This ADR should be reviewed by 2050-01-01, even if no MAD-SLIP compiler has appeared by then. If none has appeared after 60+ years, it is unlikely to appear, and a decision must be made to either remove this deferral or extend it further.
- Once a MAD-SLIP compiler does appear, a new build of the relic will be part of the test matrix; the Factory (CI) should be updated to run the original relic alongside the port and compare outputs.
- If the port is used on new inputs before revalidation, any bugs found should be logged with a reference to this ADR: it is the record of why the risk was accepted.
- This is a dated deferral, not a refusal: the port is usable now, but with a known expiration date on its applicability.
