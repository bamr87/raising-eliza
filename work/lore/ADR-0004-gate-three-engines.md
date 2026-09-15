# ADR-0004: The gate uses a three-engine design (replay, shadow, live) for safe cutover without recompilation

## Status

Accepted (chosen during gate design, 2026-09-15)

## Context

The relic (ELIZA in MAD-SLIP) cannot be run directly — no MAD-SLIP compiler exists at this dig site. The port (eliza.py in Python) has been validated against the golden transcript, showing zero mismatches across 15 turns. To move from proving the port correct to running it in production, the gate must allow users to call the modern HTTP service instead of the relic, but:

1. If the port has a bug not exercised by the golden transcript, rolling back must not require redeploying or restarting the entire service.
2. Cutover must be provable: we must know the port is answering identically to the relic on every input, not just on the 15 lines in the transcript.
3. The choice of which engine answers must be survivable as a temporary state, not baked into the binary or the routing table.

## Decision

The gate exposes three routing modes as mutually-exclusive --engine flags:

- **replay**: Serve the golden transcript turn by turn from `relic/golden/cacm_1966_conversation.txt`, per conversation. This is the closest thing to "running the relic" that is possible at this dig site. Replay does not use the message; it has nothing to run it against.

- **shadow**: Serve the replay answer to the caller (exact behavior of relic mode), but also run eliza.py in the background on the same conversation and message. Log every MATCH or MISMATCH. If all 15 turns log MATCH when fed the golden transcript in order, the port is proven equal on that transcript; the presence of any MISMATCH reveals the port's bug on live input.

- **live**: Serve eliza.py (the live port) directly from the message, with no fallback. This is the cutover state.

Cutover and rollback are the same operation: kill the process and restart with a different --engine flag. Nothing about the routing is compiled in; the choice is a startup parameter.

## Evidence

- `eliza_gate.py:10-37`: Gate docstring documents all three engines and their purpose.
- `eliza_gate.py:95-115` (Conversation class): State (MEMORY queue, per-group reassembly cycling, replay cursor) is kept per conversation_id in memory for the process lifetime, so multi-turn conversations behave identically over HTTP as they do in reconcile.py's single session.
- `eliza_gate.py:118-180` (do_POST method): The engine choice is read from self.engine, which is set once at startup via argparse. No runtime routing logic exists; the choice is baked in to process launch only.
- `test_gate.py`: The door-validation tests exercise the gate with --engine replay, proving the validation happens before any engine runs.

## Consequences

- Moving from replay to shadow requires only a restart; moving from shadow to live requires only another restart. No recompilation, no redeploy.
- The shadow mode's MATCH/MISMATCH log becomes the proof of port equality. A production shadow run on real customer input would be the evidence that the port is safe; zero mismatches gives the Council confidence; one mismatch stops the cutover and points to the bug.
- Shadow mode imposes runtime cost (every request runs both engines), so it is not a permanent state; it is a temporary proof during the cutover window.
- If the port has no bugs on the golden transcript but fails on real input (in shadow mode), this gate design makes the failure visible without breaking the caller's experience: they are served the correct relic answer while the port's bug is discovered and fixed.
