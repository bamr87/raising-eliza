# ADR-0001: This transcription of the 1966 CACM ELIZA script includes six disclosed corrections to the printed appendix

## Status

Accepted (recovered from the relic, 2026-09-15)

## Context

The file `1966_CACM_script.txt` is a 2020 reconstruction of the ELIZA script appendix published in Weizenbaum's January 1966 CACM article. Weizenbaum's original MAD-SLIP source code is lost; we have only the script data as printed and the separately-transcribed engine.

The transcriber documented six specific alterations to the printed appendix before commit. Four are editorial (whitespace, removal of comments); two are substantive corrections: six duplicate lines were removed and commented, and one missing closing bracket was added. The transcriber provides no explanation of how the errors were identified, only that they existed in the original print.

## Decision

The transcription is accepted as the canonical ELIZA script for this dig site. Any reference to "the 1966 ELIZA script" hereafter means the version at `1966_CACM_script.txt`, including these six corrections and their commented-out originals.

If a future interpreter runs this code and produces output that does not match the golden transcript (`golden/cacm_1966_conversation.txt`), any discrepancy must first be tested against the uncorrected version (restoring the duplicates and missing bracket) to determine whether the corrections themselves altered the algorithm. If output then matches, the corrections are validated; if not, the corrections are a hypothesis.

## Evidence

- `1966_CACM_script.txt:14-28`: Transcriber credits (Anthony Hay, December 2020) and explicit listing of all six alterations: whitespace addition, six duplicate-line removals, one missing-bracket addition.
- `1966_CACM_script.txt:192, 252, 322, 376, 428, 501`: The six duplicate lines are visible in place as comments, marked with their line ranges.
- `1966_CACM_script.txt:508-509`: The added closing bracket is noted in a comment.
- `1966_CACM_script.txt:35-36`: The original Weizenbaum source is confirmed as lost; this is a reconstruction from the printed 1966 appendix only.

## Consequences

- Future work depends on the corrected version. If Weizenbaum's original source were discovered, a line-by-line diff against this version should be part of the validation.
- The corrections are documented in place and can be un-done by reverting the comments; reversibility is built in.
- Any test or validation that uses the golden transcript (`cacm_1966_conversation.txt`) implicitly validates that these corrections were correct, not that the corrections are correct *in isolation*. A full interpreter is needed to separate those claims.
