# Elders of ELIZA (MAD-SLIP, IBM 7094)

| Who | Touched | When | How to reach |
|---|---|---|---|
| Joseph Weizenbaum | Original author; designed the algorithm, wrote the MAD-SLIP code, wrote the 1966 CACM paper | 1960s | Deceased (died 2008); MIT archives may hold correspondence |
| Anthony Hay | Transcribed the 1966 CACM script appendix into modern form | December 2020 | Contact likely through transcription attribution; no email provided in source |
| Anonymous annotator | Annotated the full transcription with linguistic and MAD-SLIP commentary | February 2022 (tentative; filename `20220216`) | Unknown — the annotated file provides no author name or contact info |
| Current MAD/SLIP compiler maintainers (if any exist) | Understand the original compiler behavior and semantics of the SLIP library | Current | Likely none — no MAD compiler is currently maintained; the language is effectively historical |

## Questions for the Elders (if they were reachable)

These come from EXPEDITION.md's Unknowns section:

1. **How was the transcription produced?** OCR of the 1966 CACM printed appendix, manual retyping, or from a later reimplementation? (Weizenbaum's original source is stated as lost.)

2. **What do the SLIP primitives (`HASH`, `YMATCH`, `ASSMBL`, `SEQRDR`/`SEQLR`, `LSSCPY`) actually do, bit for bit?** They are described only in prose comments in the relic; the external SLIP manual is not part of the dig site.

3. **Were the two disclosed corrections (six duplicate lines, one missing close-paren) genuine printing errors in the 1966 journal, or did they enter later?** The transcriber documents them but does not explain how they were identified as errors.

4. **Would this program, if a working MAD-SLIP compiler and SLIP runtime were reconstructed, actually reproduce `golden/cacm_1966_conversation.txt` byte-for-byte across all 15 exchanges?** (Three exchanges are hand-traced in EXPEDITION.md; the rest are unconfirmed.)

5. **Who annotated the 20220216 version, and is it the same transcriber's later revision or a different pass?** The annotated file's header does not restate authorship or date inline.

6. **Where do the annotator's own uncertainties (flagged with "???") come from?** For example, the purpose of the `MINE` variable, and control-flow closure mismatches.

## Status

- Weizenbaum is deceased.
- The transcriber (Anthony Hay) is credited by name but no contact method is available.
- The annotator is anonymous.
- No maintainer of the MAD or SLIP languages is known to be active.

This Elders roster can therefore support only documentary evidence — the source files themselves — not interviews with living people. Future researchers should check MIT's Weizenbaum archives for any surviving correspondence about the transcription or annotations.
