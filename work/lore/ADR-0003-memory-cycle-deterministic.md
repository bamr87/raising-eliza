# ADR-0003: The MEMORY mechanism uses a deterministic backward cycle because the original SLIP HASH primitive is unavailable

## Status

Accepted (reconstructed during port, 2026-09-15)

## Context

Weizenbaum's 1966 ELIZA uses a SLIP library primitive, `HASH.(BOT.(INPUT),2)+1`, to assign each captured memory to one of four memory template slots. The SLIP library is not present at this dig site — only the MAD-SLIP source code exists, and no MAD-SLIP compiler is available to run it (see EXPEDITION.md). The HASH algorithm is not documented anywhere in the relic's text files.

The port must produce the exact output of the golden transcript, including its one memory recall at turn 30, which echoes state captured at turn 5. Without knowing what HASH does, the port cannot run HASH. It must find a stand-in that produces the same output.

## Decision

The port's MEMORY mechanism uses a per-keyword deterministic counter that cycles backward through template indices 3, 2, 1, 0, 3, 2, 1, 0, ... instead of using HASH. This counter is:
- Advanced once each time the MEMORY-designated keyword (MY) is the turn's chosen keyword
- Deterministic (depends only on how many times MY has been chosen, never on message content)
- Content-independent (the same message always files its memory in the same slot, regardless of what the message says)

This is documented in eliza.py lines 51-54 as a "reconstruction, not a recovered fact".

## Evidence

- `eliza.py:42-58` ("MEMORY: whenever the MEMORY-designated keyword (MY) is the turn's chosen keyword..."): The port documents its own reconstruction, naming it as such and explaining why the original HASH is unavailable.
- `MAD-SLIP_transcription.txt:343` (LIMIT variable and recall logic): The MAD source specifies turn counter 4 as the recall trigger; the port reproduces this exactly.
- `golden/cacm_1966_conversation.txt` turns 5/6 and 30: Turn 5 plants the memory "boyfriend made me/you come here"; turn 30 recalls it verbatim. The port's backward-cycle counter reproduces this exact recall.
- `reconcile.py` output: Running the full golden transcript with this reconstruction produces zero mismatches, validating the counter against the one memory recall available.

## Consequences

- This port is correct *for the golden transcript*, not *for the original ELIZA*. If Weizenbaum's original MAD-SLIP source were ever recovered and run on a MAD-SLIP compiler, the original HASH algorithm might assign memories to slots in a different order, producing different outputs on inputs not in the golden transcript.
- Any port of ELIZA to another language should use this same deterministic counter, not attempt to guess HASH's algorithm or implement a non-deterministic replacement. The goal is to match this port, which matches the transcript.
- Once a MAD-SLIP compiler becomes available and the original relic can be run, this ADR should be revisited: the counter can then be validated or replaced against the actual relic's behavior on new inputs.
