# ADR-0002: NEWKEY retry functionality is not implemented in this transcribed engine; failed decompositions print the literal string "NEWKEY"

## Status

Accepted (recovered from the relic, 2026-09-15)

## Context

Weizenbaum's 1966 CACM paper describes a `NEWKEY` escape hatch as optional reassembly output: if a decomposition rule matches but its selected reassembly is `(NEWKEY)`, the system should discard the current keyword match and retry with the next-highest-precedence keyword.

The MAD-SLIP engine in this relic (`MAD-SLIP_transcription.txt`) does not implement this control flow. Instead, when a reassembly is `(NEWKEY)`, the system prints the literal text string "NEWKEY" as part of the response, and does not retry with a lower-precedence keyword.

This is a known architectural reduction from Weizenbaum's design, confirmed by the annotator of the 20220216 version.

## Decision

The engine as transcribed is accepted for all future work and validation. References to "what ELIZA does" mean what this engine does, not what Weizenbaum's design doc describes.

If any test of the golden transcript produces unexpected behavior involving `NEWKEY` (either as literal output or as a retry failure), this ADR is the first place to check: the engine is architecturally incapable of implementing the retry.

## Evidence

- `ELIZA_transcription_annotated_20220216.txt:704-712`: Annotator's explicit note: "This code does not support the NEWKEY functionality he [Weizenbaum] describes."
- `MAD-SLIP_transcription.txt:377` (the `HIT` routine): The decomposition/reassembly logic evaluates each reassembly rule in order; no special control-flow handling exists for `NEWKEY` as a keyword. If the reassembly text is `(NEWKEY)`, it prints that literal text via `TPRINT`.
- `1966_CACM_script.txt:184, 200, 538`: The literal string `(NEWKEY)` appears in script data (as reassembly rules), confirming the script authors expected it to be usable. But `grep -n NEWKEY relic/MAD-SLIP_transcription.txt` returns zero matches in the program code — no label, no branch target, no control-flow keyword.
- `1966_CACM_script.txt:9-39`: Weizenbaum's paper describes the optional `NEWKEY` escape hatch and its semantics (retry with next keyword). The transcribed code implements neither the check nor the retry.

## Consequences

- Any port of this engine to a modern language must replicate this behavior exactly, not implement Weizenbaum's design. The golden transcript (`cacm_1966_conversation.txt`) is the proof: if a port produces the same output, it is correct *for this transcribed version*, regardless of what the 1966 paper says it should do.
- If future work discovers that Weizenbaum's original engine actually *did* implement NEWKEY, then this transcribed version is incomplete and a new ADR is needed.
- The three hand-traced exchanges in EXPEDITION.md do not exercise any `(NEWKEY)` reassembly rules, so they do not validate this reduction. This is a gap in the validation, not a contradiction.
