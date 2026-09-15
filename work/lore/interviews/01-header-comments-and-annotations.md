# Interview: The Relic's Header Comments and Annotations — Standing in for Weizenbaum and Anthony Hay

## Consent

This is a lab artifact; the source documents (header comments in `1966_CACM_script.txt`, annotations in `ELIZA_transcription_annotated_20220216.txt`) are in the public domain or under standard open-license attribution. The relic itself provides these statements directly.

## Q: What is this code, and why does it exist?

### Elder's words (from `1966_CACM_script.txt:1-12`)

> Transcribed from Joseph Weizenbaum's article on page 36 of the January 1966 edition of Communications of the ACM titled 'ELIZA - A Computer Program For the Study of Natural Language Communication Between Man And Machine'.
> 
> "Keywords and their associated transformation rules constitute the SCRIPT for a particular class of conversation. An important property of ELIZA is that a script is data; i.e., it is not part of the program itself." -- From the above mentioned article.
> 
> Transcribed by Anthony Hay, December 2020

### Interpretation

The code is a reconstruction of Weizenbaum's original ELIZA system, written in MAD-SLIP for the IBM 7094. Weizenbaum designed ELIZA to separate the algorithm (the program code) from the domain knowledge (the script data). This separation allows the same engine to run different conversational domains by swapping the script.

Confirmed by: the separation of `MAD-SLIP_transcription.txt` (the engine: `CHANGE`, `TPRINT`, `LPRINT`, `TESTS`, `DOCBCD`, `ELIZA` routines) from `1966_CACM_script.txt` (the script data: keyword table and decomposition/reassembly rules).

## Q: Is this the original 1960s code, and how certain should we be?

### Elder's words (from `1966_CACM_script.txt:19-28, 35-38`)

> This is a verbatim transcription of the ELIZA script in the above mentioned CACM article, with the following caveats:
> a) Whitespace has been added to help reveal the structure of the script.
> b) In the appendix six lines were printed twice adjacent to each other (with exactly 34 lines between each duplicate), making the structure nonsensical. These duplicates have been commented out of this transcription.
> c) One closing bracket has been added and noted in a comment.
> d) There were no comments in the script in the CACM article.
> 
> Weizenbaum was written in MAD-Slip. It seems his original source code has been lost. Weizenbaum developed a library of FORTRAN functions for manipulating doubly-linked lists, which he called Slip (for Symmetric list processor).

### Interpretation

This is not the original 1966 code, but a 2020 reconstruction from the 1966 CACM printed appendix. The transcriber (Anthony Hay) explicitly documented six editorial corrections: whitespace addition, removal of six duplicated lines, addition of one missing closing bracket, and removal of original comments. The original MAD-SLIP source code is stated as lost.

This means:
1. We are working from an OCR'd or manually transcribed version of a 1966 printed journal appendix.
2. Hay's corrections are disclosed and can be verified (the duplicates are marked in comments; the added bracket is noted).
3. The original MAD-SLIP program that Weizenbaum ran is not available; we have only the script data and a separately-transcribed MAD-SLIP engine.

Confirmed by: the explicit caveat list and the visible duplicate-line comments at `1966_CACM_script.txt:192, 252, 322, 376, 428, 501`.

## Q: Why is the NEWKEY functionality not implemented in the code?

### Elder's words (from `ELIZA_transcription_annotated_20220216.txt:704-712`)

> This code does not support the NEWKEY functionality [Weizenbaum] describes.

### Interpretation

Weizenbaum's 1966 CACM paper describes a `NEWKEY` escape hatch that would allow the system to retry with the next-highest-precedence keyword if a decomposition rule fails. The MAD-SLIP engine at `MAD-SLIP_transcription.txt` does not implement this. Instead, if a decomposition fails to match and the only branch is `(NEWKEY)`, the system prints the literal text "NEWKEY" as output rather than retrying.

This is a known reduction from Weizenbaum's design. The code is architecturally consistent: `NEWKEY` appears only in script *data* (`1966_CACM_script.txt:184, 200, 538`), never as a label or branch target in the program (`grep -n NEWKEY relic/MAD-SLIP_transcription.txt` returns zero code-level matches).

Confirmed by: explicit annotation and grep verification.

## Q: How were the corrections to the 1966 CACM printed appendix identified and applied?

### Interpretation

The transcriber identified two classes of corrections:
1. Six duplicate lines (each duplicated with exactly 34 lines between occurrences) that made the structure nonsensical — these were commented out rather than deleted, allowing verification.
2. One missing closing bracket — noted in a comment with its location.

The transcriber does not explain how they determined these were errors (printing failures) rather than intentional. However, the duplicates' exact spacing and structural duplication strongly suggest a printing error (a line or block was accidentally printed twice). The missing bracket was likely identified by attempting to parse the structure and finding an imbalance.

Confirmed by: the visible duplicated lines in comments and the consistent structure of the S-expressions after the corrections are applied.

## Q: Do the three hand-traced exchanges confirm the code works as intended?

### Elder's words (from EXPEDITION.md:89-109)

> Manual trace of the golden transcript against the script rules reproduces three consecutive exchanges exactly:
> - Turn 1→2: keyword `ALIKE` has explicit precedence 10 and out-ranks the unranked keyword `ARE`, so `ALIKE` wins, links to `=DIT`, and `DIT`'s first reassembly is literally `(IN WHAT WAY)`.
> - Turn 3→4: keyword `ALWAYS`, catch-all decomposition `(0)`, first reassembly is literally `(CAN YOU THINK OF A SPECIFIC EXAMPLE)`.
> - Turn 5→6: `MY` is keyword-substituted to `YOUR` in place; `ME` is a plain substitution-only keyword; the decomposition reassembles as exactly "YOUR BOYFRIEND MADE YOU COME HERE".

### Interpretation

Three consecutive exchanges from the 1966 CACM conversation (`golden/cacm_1966_conversation.txt:1-6`) were hand-traced through the script rules and the MAD-SLIP engine logic, and all three produced the exact output shown in the golden transcript. This confirms:

1. The keyword precedence rule (highest-ranked keyword wins) is correctly modeled in the code.
2. The decomposition/reassembly logic is architecturally sound.
3. The keyword substitution and scanning delimiters work as documented.

This is consistent with the code producing the golden transcript, but it is not a proof — only three of fifteen exchanges are traced. A full interpreter would be needed to verify all fifteen.

Confirmed by: the three traces in EXPEDITION.md:89-109, which cite specific line numbers in both the script and the engine.

## Still Unknown

- The full semantics of the SLIP library primitives (`HASH`, `YMATCH`, `ASSMBL`, `SEQRDR`, `SEQLR`, `LSSCPY`).
- Whether the program produces the full 15-exchange golden transcript without a real MAD-SLIP interpreter.
- The identity of the annotator and how the 20220216 revision relates to the December 2020 transcription.
- Details of which uncertainties marked with "???" in the annotations remain unresolved.
