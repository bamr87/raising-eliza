# ADR-0007: Reassembly cycle counters and turn trace live on the session, not the parsed script

## Status

Accepted (housing / observability, 2026-09-15)

## Context

`Script` is the DOCTOR data. Reassembly `next_alt` counters are conversational state. They used to sit on the parsed rule groups, so the data object mutated as people talked. Two `Eliza()` sessions were already isolated only because each re-parsed the file.

Operators also could not see which keyword produced a reply without reading the scan by hand. That is housing, not personality.

## Decision

Each `Eliza` clones rule groups at construction and mutates only the clone. `respond()` still returns the reply string. It also records `last` (keyword, substituted sentence, source, MEMORY flags). The gate may send `trace` as an additive `/say` field on live/shadow. Replies, NEWKEY, and MEMORY selection are unchanged.

## Evidence

- `eliza.py` `Eliza.__init__`: `self.rules = {k: _clone_rule(v) for k, v in self.script.rules.items()}`.
- `eliza.py` `respond`: return value is still the assembled reply; `self.last` is written after.
- `test_eliza.py` `test_sessions_do_not_share_reassembly_cycles`: two sessions both answer `IN WHAT WAY` to the first ALIKE turn.
- `reconcile.py` / golden turn trials: the 15 published turns still tie out.

## Consequences

- Sharing one `Script` object across sessions is now safe; cycle state cannot leak through it.
- Callers that reject unknown JSON keys on `/say` must ignore `trace`.
- Personality remains `relic/1966_CACM_script.txt`. Trace must never be used as a lookup table for replies.
