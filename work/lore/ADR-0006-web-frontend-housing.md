# ADR-0006: The web frontend is housing; POST /say remains the door and engines stay a startup flag

## Status

Accepted (housing modernization, 2026-09-15)

## Context

The gate already speaks HTTP (ADR-0004) with three engines selected at process start. Interactive use still required curling POST /say or running `eliza.py` on stdin. A browser UI is housing around the same engines, not a new personality and not a rewrite of the port.

The door invariant must survive: a bad POST /say is refused before any engine runs. Extra routes must not move a conversation's replay cursor or MEMORY queue.

## Decision

The gate serves a stdlib static UI at GET `/` and additive JSON under `/api/`. Engine selection remains `--engine` at startup. POST `/say` keeps its required body and the fields `conversation_id`, `engine`, and `reply`; extra keys (`turn`, `memory`, `replay_next`, and shadow `live`/`match`) are additive. Creating or listing conversations, reading status, and serving HTML do not call `replay_reply()` or `live_reply()`.

## Evidence

- `eliza_gate.py` `do_POST`: `/say` still calls `parse_say_request` and returns 400 before `_conversation` / engine methods.
- `eliza_gate.py` `do_GET`: `/`, `/api/status`, `/api/golden`, and `/api/conversations` never call `replay_reply` or `live_reply`.
- `test_gate.py` `test_a_refused_request_never_advances_conversation_state`: the original door leak-check still holds.
- `test_gate.py` `test_get_does_not_run_an_engine`: GET `/api/status` then POST `/say` still returns golden turn 1.
- `work/static/index.html`: the UI is static housing that calls the existing `/say` contract.

## Consequences

- Opening the UI does not by itself walk the golden transcript or mutate MEMORY.
- Callers that only read `reply` keep working; callers that reject unknown JSON keys need to ignore the additive fields.
- Changing personality still means editing `relic/1966_CACM_script.txt`, not the HTML.
- Runtime engine switching is still out of scope (ADR-0004).
