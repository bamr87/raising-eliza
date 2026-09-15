# Expedition log: ELIZA (MAD-SLIP, IBM 7094)

Dig site: `relic/1966_CACM_script.txt`, `relic/MAD-SLIP_transcription.txt`,
`relic/MAD-SLIP_translation.txt`, `relic/ELIZA_transcription_annotated_20220216.txt`,
`relic/MAD_Primer.pdf`, reconciliation target `relic/golden/cacm_1966_conversation.txt`.

**No MAD-SLIP compiler exists** (confirmed: `which mad madcc mad-compiler` → no hits,
and no such package is installed). Every claim below that is marked Evidence was
checked by reading the relic's own text, by cross-referencing it against the
independent primary source (`MAD_Primer.pdf`, via `pdftotext` + `grep`), or by
hand-tracing the documented algorithm against the golden transcript — never by
running the program, because running it is not possible here.

## Evidence (seen in the relic, or independently cross-checked)

- **What this is.** A retyped/reconstructed source for Joseph Weizenbaum's ELIZA,
  written in MAD-SLIP for an IBM 7094, per the header comment block —
  `relic/1966_CACM_script.txt:1-38` and the title line
  `relic/ELIZA_transcription_annotated_20220216.txt:1-6`. The header states plainly:
  "It seems his original source code has been lost" (`1966_CACM_script.txt:35-36`).
  So this file is a *reconstruction*, not the literal 1966 artifact.

- **The transcriber documents his own edits to the script.** `1966_CACM_script.txt:19-28`
  states six lines were duplicated in the original 1966 CACM printed appendix and were
  commented out here, and one missing closing bracket was added. The removed duplicates
  are visible in place as comments at `1966_CACM_script.txt:192, 252, 322, 376, 428, 501`,
  and the added-bracket note is at `1966_CACM_script.txt:508-509`. This means the script
  file already has known, disclosed corrections layered onto the original — not raw 1966 text.

- **The script grammar (six rule forms, R1–R6) is documented in the relic itself**,
  with page citations back to the 1966 CACM article — `1966_CACM_script.txt:63-150`.
  Examples given there (e.g. `(MY = YOUR 2 ...)`) match rules that actually appear later
  in the same file, e.g. `1966_CACM_script.txt:451-461`.

- **Program structure.** `MAD-SLIP_transcription.txt` contains five `MAD` routines:
  `CHANGE` (lines 4-92), `TPRINT` (93-127), `LPRINT` (128-163), `TESTS` (164-197),
  `DOCBCD` (198-208), and the main program `ELIZA` (209-412). The annotated copy
  (`ELIZA_transcription_annotated_20220216.txt`) is the same code with prose commentary
  interleaved, generally referring to the code block just above it (stated at its own
  header, lines 4-6).

- **MAD-language abbreviations used in the code check out against the primary
  reference manual.** I ran `pdftotext relic/MAD_Primer.pdf` and grepped
  Appendix A ("Allowable Abbreviations in MAD", `work/mad_primer.txt:6313` on)
  and confirmed exact matches for every abbreviation the relic uses:
  `W'R`=WHENEVER, `T'H`=THROUGH, `T'O`=TRANSFER TO, `V'S`=VECTOR VALUES,
  `E'L`=END OF CONDITIONAL, `E'N`=END OF FUNCTION, `E'M`=END OF PROGRAM,
  `O'E`=OTHERWISE, `O'R`=OR WHENEVER, `D'N`(as `DIMENSION` keyword in the code,
  spelled out) and `F'N`=FUNCTION RETURN, `N'R`↔`NORMAL MODE IS INTEGER`
  (`work/mad_primer.txt:6313-6470`). This matches what the annotator independently
  claims inline, e.g. `ELIZA_transcription_annotated_20220216.txt:227-229, 366-367,
  410-414` — and I verified it against the manual myself rather than trusting the
  annotation alone.

- **Octal-constant syntax checks out.** `MAD_Primer.pdf` §2.1.5
  (`work/mad_primer.txt:876-878`) says octal constants are written as 12-digit octal
  numbers followed by `K`. The relic's `LPRINT` routine defines
  `LEFTP = 606074606060K`, `RIGHTP= 606034606060K`, `BOTH = 607460603460K`
  (`MAD-SLIP_transcription.txt:134-136`) — each is exactly 12 octal digits + `K`.
  These render the box-drawing brackets used when a script is written back out.

- **`$`-delimited string literals check out.** `MAD_Primer.pdf` §2.1.3
  (`work/mad_primer.txt:843-845`) says alphabetic constants are 1-6 characters
  bounded by `$`. This matches every string literal in the relic, e.g.
  `$PLEASE INSTRUCT ME$` (`MAD-SLIP_transcription.txt:13`) and the keyword table
  `$TYPE$,$SUBST$,$APPEND$,$ADD$,$START$,$RANK$,$DISPLA$` (`MAD-SLIP_transcription.txt:9-10`).

- **The list-processing calls (`SEQRDR`, `NEWBOT`, `POPTOP`, `HASH`, `LIST.`,
  `TXTPRT`, `YMATCH`, `ASSMBL`, …) are not native MAD statements.** MAD's own
  built-in list/stack facility is the "List Manipulation Statements" section of the
  primer (`SET LIST TO`, `SAVE DATA`, `SAVE RETURN`, `RESTORE DATA` —
  `work/mad_primer.txt:1894` on), which is a completely different, simpler
  fixed-vector stack API. None of the relic's SLIP calls appear there. This is
  consistent with, and independently supports, the header claim that Weizenbaum
  "developed a library of ... functions for manipulating doubly-linked lists,
  which he called Slip" as a separate add-on (`1966_CACM_script.txt:36-38`).

- **The `NEWKEY` escape hatch described in Weizenbaum's CACM paper is not
  implemented as a control-flow keyword in this code.** The annotator flags this
  explicitly (`ELIZA_transcription_annotated_20220216.txt:704-712`: "this code does
  not support the NEWKEY functionality he describes"). I checked this independently:
  `grep -n NEWKEY relic/MAD-SLIP_transcription.txt` returns **zero matches** — the
  literal word `NEWKEY` appears only inside script *data*
  (e.g. `1966_CACM_script.txt:184, 200, 538`), never as a label or branch target in
  the program code. If a rule whose reassembly is `(NEWKEY)` is ever selected, the
  matching/assembly routine (`HIT`, `MAD-SLIP_transcription.txt:377`) would print the
  literal text "NEWKEY" rather than retrying with the next-highest-precedence keyword.

- **Manual trace of the golden transcript against the script rules reproduces
  three consecutive exchanges exactly**, without running any program:
  - Turn 1→2 (`golden/cacm_1966_conversation.txt:1-2`, "Men are all alike." →
    "IN WHAT WAY"): keyword `ALIKE` has explicit precedence 10
    (`1966_CACM_script.txt:216`) and out-ranks the unranked keyword `ARE`
    (`1966_CACM_script.txt:291`, implicit precedence 0), so `ALIKE` wins, links to
    `=DIT` (`1966_CACM_script.txt:216-217`), and `DIT`'s first reassembly is literally
    `(IN WHAT WAY)` (`1966_CACM_script.txt:542`).
  - Turn 3→4 ("They're always bugging us..." → "CAN YOU THINK OF A SPECIFIC EXAMPLE"):
    keyword `ALWAYS` (`1966_CACM_script.txt:527-532`), catch-all decomposition `(0)`,
    first reassembly is literally `(CAN YOU THINK OF A SPECIFIC EXAMPLE)`.
  - Turn 5→6 ("Well, my boyfriend made me come here." → "YOUR BOYFRIEND MADE YOU COME
    HERE"): `,` is a scan delimiter (`MAD-SLIP_transcription.txt:270`), so "Well,"
    is discarded before any keyword is found. `MY` is keyword-substituted to `YOUR`
    in place (`1966_CACM_script.txt:451`, precedence 2); `ME` is a plain
    substitution-only keyword `(ME = YOU)` (`1966_CACM_script.txt:334`) that rewrites
    "ME"→"YOU" during the same left-to-right scan without overriding the already-found
    keyword. The decomposition `(0 YOUR 0)` (no `FAMILY`-tagged word present, so the
    family-specific first rule at `1966_CACM_script.txt:452` is skipped) reassembles as
    `(YOUR 3)` = "YOUR" + everything after it in the now-substituted input, producing
    exactly "YOUR BOYFRIEND MADE YOU COME HERE" (`1966_CACM_script.txt:457-458`).

- **`golden/cacm_1966_conversation.txt`** is a 30-line, 15-exchange dialogue matching
  the sample conversation printed in Weizenbaum's January 1966 CACM article — this is
  the file the chapter names as "the reconciliation target," and it is what the three
  traces above were checked against.

## Hypotheses (inferred, not fully verified)

- The script and matching algorithm most likely reproduce the *entire* golden
  transcript, not just the three exchanges I hand-traced above — I did not trace all
  15 turns (e.g. the `MEMORY`/`MY` recall at turn 30, or the `AM`/`I`/`YOU`
  pronoun-swap chains in turns 15-27), so this remains unconfirmed.

- The annotator's claim that ELIZA's `MEMORY` selection is **deterministic** (chosen by
  `HASH` of the last input word) rather than random, contradicting Weizenbaum's own
  1966 prose ("selection ... is random") — `ELIZA_transcription_annotated_20220216.txt:751-756`
  — is plausible from the code shape (`HASH.(BOT.(INPUT),2)+1` at
  `MAD-SLIP_transcription.txt:327`) but I cannot verify it, because the `HASH`
  function's actual algorithm is part of the separate SLIP library and is not present
  in any file at this dig site.

- The explanation that keyword matching can silently break on words longer than six
  characters, because of 7094 36-bit-word / 6-bit-character packing
  (`ELIZA_transcription_annotated_20220216.txt:186-211`), is architecturally plausible
  and matches real 7094 hardware, but I can't exercise the `TESTS` routine to see it
  happen.

- The four files (raw script, plain transcription, "translated"/modernized
  transcription, and annotated transcription) are presented as consistent views of one
  artifact. I spot-checked overlapping passages (e.g. the `CHANGE` and `ELIZA` routines
  appear near-identically in `MAD-SLIP_transcription.txt` and
  `MAD-SLIP_translation.txt`) and found them consistent, but did not diff every line of
  all four files against each other.

## Unknowns (questions only a person or another document could answer)

- Weizenbaum's original MAD-SLIP source is stated as lost
  (`1966_CACM_script.txt:35-36`). Every file here is a modern reconstruction/transcription
  — how was it produced (OCR of the printed listing? manual retyping? from a later
  reimplementation?), and how confident should we be that it compiles to the same
  behavior as the 1960s original, even setting aside that no compiler is available to
  test it?
- What do the SLIP primitives (`HASH`, `YMATCH`, `ASSMBL`, `SEQRDR`/`SEQLR`, `LSSCPY`,
  `TESTS`'s full semantics) actually do, bit for bit? They're described only in prose
  comments here; the annotator points to an external SLIP manual
  (`ELIZA_transcription_annotated_20220216.txt:372-373`, a Google Drive link) that is
  not part of this dig site.
- Were the two disclosed corrections to the 1966 CACM script (six duplicate lines, one
  missing close-paren — `1966_CACM_script.txt:19-28`) genuine printing errors in the
  original journal, or did they enter later in some other transcription pass? Nothing
  here documents how the transcriber determined they were errors rather than
  intentional.
- Would this program, if a working MAD-SLIP compiler and SLIP runtime were reconstructed,
  actually reproduce `golden/cacm_1966_conversation.txt` byte-for-byte across all 15
  exchanges? The three-exchange hand trace above is consistent with it, but a hand trace
  is not an execution — this is exactly the kind of claim that needs a real interpreter
  to settle, and the condition of the dig is that one does not exist here.
- Who transcribed each file, and are their dates/versions consistent with each other?
  `1966_CACM_script.txt:14` credits "Anthony Hay, December 2020"; the annotated file is
  named with a `20220216` date but its own header does not restate authorship or date
  inline — is it the same transcriber's later revision, or a different pass?
- The annotator flags several of their own uncertainties inline with "???"
  (e.g. purpose of the `MINE` variable, `ELIZA_transcription_annotated_20220216.txt:382`;
  why `E'L` at line 001750 closes the `O'E` at line 001270,
  `ELIZA_transcription_annotated_20220216.txt:869-870`) — these are open questions even
  for the person who did the closest reading of this code, not just for me.

## Chapter V: the port and the ledger

`work/eliza.py` parses `relic/1966_CACM_script.txt` at construction time (the
`Script` class) into the same rule table `parse_script.py` already validated
in Chapter II -- substitutions, precedence, DLIST tags, decomposition
groups with per-`(keyword, group)` reassembly cycling, R4 links, R5 PRE,
MEMORY, NONE -- then runs the algorithm the header documents. No reply text
from `golden/cacm_1966_conversation.txt` appears anywhere in `eliza.py`;
`work/reconcile.py` runs the port as one continuous session over the
golden master's 15 USER lines and prints a turn-by-turn ledger. Current
result, run 2026-09-15: **RECONCILED, 0/15 mismatches** (`python3
reconcile.py`, exit 0), and the pre-existing `test_eliza.py` characterization
suite (written before `eliza.py` existed, Chapter IV-style) passes all 19
trials unmodified.

Three algorithmic points the MAD source and the header comment leave
genuinely underdetermined -- confirmed as unresolved Hypotheses earlier in
this document -- had to be decided to make the port runnable at all. Each
decision is recorded in `eliza.py`'s own module docstring; summarized here
for the Lore:

- **Where substitution happens.** Not shown in the ELIZA main loop
  (`MAD-SLIP_transcription.txt:263-325`) at all; traced instead to the
  `TESTS` function's `SUBST`/`INSRT` branch (`:180-202`), which rewrites the
  live input list in place for *every* scanned word that names a
  substituting rule, not only the eventual chosen keyword. Verified by hand
  against golden turns 3 (`MY`+`ME` both substitute; `MY` wins on
  precedence), 11 and 21 (`YOU` substitutes to `I` even though `YOU` itself,
  not `ARE`, is the word that ends up ranked) -- both hand traces reproduced
  by the running port.
- **Per-rule reassembly cycling is per `(keyword, decomposition-group)`,
  shared across however many keywords link into it.** Verified against four
  independent golden turns: `MY`'s family-tagged group is used at turns
  7/8/9/14 (of `reconcile.py`'s 1-indexed turns) and cycles through all four
  of its own alternatives in order; `DIT`'s group is reached twice, once via
  `ALIKE` (turn 1) and once via `LIKE` (turn 10), and correctly continues
  its own cycle rather than resetting -- this was the strongest single piece
  of evidence for the whole reassembly model, since it rules out
  "one counter per keyword" as well as "one counter per group per
  entry-point."
- **MEMORY template selection.** The MAD source computes it with
  `HASH.(BOT.(INPUT),2)+1` (`:340`), a call into the SLIP library's `HASH`
  primitive, whose algorithm is not present anywhere at this dig site (see
  Hypotheses, above) and cannot be exercised without a MAD-SLIP interpreter.
  `eliza.py` instead uses a disclosed reconstruction: a dedicated counter
  that starts at the *last* template and cycles backward, independent of
  every other cycling counter. This is not a recovered fact -- it is
  whatever makes the one memory recall in the golden transcript (turn 30,
  filed under `MY` at turn 5's "boyfriend" sentence) come out right, and it
  has not been, and cannot currently be, checked against a second recall,
  because the golden transcript only contains one. Flagged the same way in
  `eliza.py`'s own docstring, not quietly assumed.

None of this required looking at `golden/cacm_1966_conversation.txt`'s reply
text while writing the matching/reassembly code -- the golden master was
read only by `reconcile.py`, after `eliza.py` was written, to check the
port's output against it. The MEMORY selection counter is the one place a
free parameter was tuned by testing against the golden master's one data
point rather than derived from a documented source; everything else in the
port follows directly from the script's own header grammar and the MAD
source's confirmed control flow.
