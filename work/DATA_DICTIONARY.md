# Data Dictionary: the ELIZA/DOCTOR script (`relic/1966_CACM_script.txt`)

This is the copybook for the relic examined in Chapter I. It is not a
fixed-width byte layout — it is a small S-expression grammar, and it
documents *itself*: the header comment at `1966_CACM_script.txt:63-150`
gives six rule forms (R1–R6) plus a NONE rule, each with a page citation
back to Weizenbaum's January 1966 CACM article. Every row below is one
construct from that grammar. EVIDENCE cites either a script line number,
or a count from `profile.txt` (the output of `parse_script.py` run against
`relic/1966_CACM_script.txt`), or both. Anything not stated by the header
comment or confirmed by the parser's counts is marked **HYPOTHESIS**.

The header's own page citations (`page 38 (a)`, `page 41 (j)`, etc.) are
reproduced as EVIDENCE because the relic states them — I have not seen the
original January 1966 CACM pages myself, so I cannot independently confirm
the page numbers are correct, only that the relic asserts them.

All counts below were produced by running:
```
python3 parse_script.py relic/1966_CACM_script.txt > profile.txt
```
on 2026-09-15, Python 3.12 (`python3 --version`), against the exact file
at `relic/1966_CACM_script.txt` (16,729 bytes, 554 lines). The full output
is saved as `profile.txt` in this directory.

## Top-level file structure

| Construct | Syntax | Meaning | Evidence |
|---|---|---|---|
| Comment line | `; ...` | Full-line comment; not part of the script data | Every comment in the file starts with `;` in column 0, no leading whitespace — checked with `sed -n '<n>p' \| cat -A` on lines 1, 192, 252, 322, 376, 428, 501, 508, 509, 553; header block itself is `1966_CACM_script.txt:1-38` |
| Greeting message | `(HOW DO YOU DO.  PLEASE TELL ME YOUR PROBLEM)` | DOCTOR's opening line, a plain word list, first top-level form | `1966_CACM_script.txt:154`; `parse_script.py` reads it as `forms[0]` |
| `START` | bare atom, not inside parentheses | Marks the boundary between the greeting and the keyword-rule list | `1966_CACM_script.txt:156`. HYPOTHESIS: the script itself never states what `START` *does* — the header grammar section (`:31-150`) never mentions it. I infer "boundary marker" only from its position (between the greeting and the first keyword rule) and from its name; no comment in this file defines its runtime behavior. |
| Keyword rule | `(KEYWORD ...)`, one of forms R1–R6 below | One entry in the DOCTOR rule table | 66 keyword rules + 1 `MEMORY` + 1 `NONE` = 68 forms between `START` and the closing `()`, confirmed by `grep -n '^(' relic/1966_CACM_script.txt \| wc -l` = 70 total top-level `(`-lines, minus the greeting and the final empty list = 68; `profile.txt` line 2: "Top-level keyword/MEMORY/NONE forms: 68" |
| Closing empty list | `()` | Terminates the script | `1966_CACM_script.txt:551`. HYPOTHESIS: meaning inferred from position (last form in the file) and the fact the header grammar never describes a "terminator" construct — no comment states this is required or what happens if it's absent. |

## Lexical elements

| Token | Meaning | Evidence |
|---|---|---|
| `(` `)` | List delimiters (S-expression), can be glued to an adjacent word with no whitespace | Header: "the script has the form of a series of S-expressions" (`:31`); glued example `DLIST(/BELIEF)` at `1966_CACM_script.txt:220` has no space before `(` |
| Bare word (atom) | A literal token: a keyword, an English word, or punctuation like `.` or `,` attached to a word | e.g. `REALLY,` at `1966_CACM_script.txt:191`, `DO.` in the greeting at `:154` |
| Digit atom, e.g. `2`, `10`, `50` | Either a rule **precedence** (when it appears right after the keyword/substitution) or a **backreference** to a decomposition-match segment (when it appears inside a reassembly rule) — same token shape, meaning decided entirely by position | Header explains backreference use at `:54-60`; precedence use at `:66` (`[precedence]` in the R1 grammar) |
| `0` | Inside a decomposition pattern: "matches zero or more words in the input" | `1966_CACM_script.txt:54-55`, worked example `:55-60`. `profile.txt`: 98 total `0` wildcards counted across all decomposition patterns |
| `=` | Operator, used in two unrelated positions: (a) `KEYWORD = SUBSTITUTION` right after a keyword, (b) `(=TARGET)` as a whole reassembly/body item meaning "link to another keyword's rules" | Position (a): header grammar `[= keyword_substitution]` at `:66`, e.g. `(MY = YOUR 2 ...)` at `:451`. Position (b): header grammar `(= equivalence_class)` at R4, `:102`, e.g. `(HOW (=WHAT))` at `:214` |
| `/` prefix inside a nested list, e.g. `(/FAMILY)`, `(/ FAMILY)` | Tag-match: matches a word carrying a given `DLIST` tag | Header R3 grammar `DLIST (/ <word> ... <word>)` at `:92-93`; used inside a decomposition pattern at e.g. `1966_CACM_script.txt:452` `(0 YOUR 0 (/FAMILY) 0)`. `profile.txt`: 3 decomposition patterns use a tag-match |
| `*` prefix inside a nested list, e.g. `(*SAD UNHAPPY DEPRESSED SICK)` | Word-class match: matches any one literal word from the list | HYPOTHESIS-adjacent: the header's grammar section (`:63-150`) never formally defines the `*` construct on its own — it only appears inside the R1 worked example at `:78` (`(0 YOUR 0 (*SAD UNHAPPY DEPRESSED SICK ) 0)`) with no prose explanation of what `*` means. I infer "OR of literal words" from that example plus its 6 real occurrences in the script data (`1966_CACM_script.txt:357,364,369,388,512,535`), all of which sit where a single matched word is expected. `profile.txt`: 6 decomposition patterns use a class-match |
| `;` at start of line | Comment | See "Comment line" above |

## The six rule forms (R1–R6) plus NONE

Every row cites the header's own definition, then the count `parse_script.py` found for that form among the 68 keyword-level forms.

| Form | Grammar (as stated in the relic) | Worked example in the relic | Evidence (header) | Count found by profiler |
|---|---|---|---|---|
| **R1** — plain transformation rule | `(keyword [=sub] [precedence] ((decomp)(reassembly)(reassembly)...) ...)` | `(MY = YOUR 2 ((0 YOUR 0 (/FAMILY) 0) ...))` — this is the *header's illustrative example*, not identical to the real `MY` rule later in the file (see Anomalies below) | `1966_CACM_script.txt:65-81`, cited as "page 38 (a)" | 29 rules classified `R1/R5-decomposition` (form label also covers R5, see below) — `profile.txt` "Decomposition rules (R1/R5, keyword != NONE): 29", with 54 total decomposition-pattern groups and 211 total reassembly alternatives across them |
| **R2** — simple word substitution, no further rules | `(keyword = keyword_substitution)` | `(DONT = DON'T)`, `(ME = YOU)` | `1966_CACM_script.txt:84-88`, cited as "page 39 (a)" | 6 rules: `DONT`, `CANT`, `WONT`, `ME`, `MYSELF`, `YOURSELF` — `profile.txt` "R2-substitution 6" |
| **R3** — word tags via `DLIST`, optional substitution | `(keyword [=sub] DLIST(/ <word> ... <word>))` | `(FEEL DLIST(/BELIEF))`, `(MOM = MOTHER DLIST(/ FAMILY))` | `1966_CACM_script.txt:91-97`, cited as "page 41 (j)" | 12 rules — `profile.txt` "R3-DLIST 12"; tags used: `BELIEF` (4×: `FEEL`,`THINK`,`BELIEVE`,`WISH`), `NOUN` (2×: `MOTHER`,`FATHER`), `FAMILY` (8×: `MOTHER`,`MOM`,`DAD`,`FATHER`,`SISTER`,`BROTHER`,`WIFE`,`CHILDREN`) |
| **R4** — link to another keyword's rule set | `(keyword [=sub] [precedence] (= equivalence_class))` | `(HOW (=WHAT))`, `(DREAMED = DREAMT 4 (=DREAMT))` | `1966_CACM_script.txt:100-107`, cited as "page 40 (c)" | 19 rules — `profile.txt` "R4-link 19": `DREAMED`, `DREAMS`, `HOW`, `WHEN`, `ALIKE`, `SAME`, `CERTAINLY`, `MAYBE`, `DEUTSCH`, `FRANCAIS`, `ITALIANO`, `ESPANOL`, `MACHINE`, `MACHINES`, `COMPUTERS`, `WERE`, `EVERYBODY`, `NOBODY`, `NOONE` |
| **R5** — pre-transform then link | `(keyword [=sub] ((decomp) (PRE (reassembly) (=equivalence_class))))` | `(YOU'RE = I'M ((0 I'M 0) (PRE (I ARE 3) (=YOU))))` | `1966_CACM_script.txt:110-117`, cited as "page 40 (f)" | Structurally identical to R1 (a decomposition + a reassembly-alternatives list), distinguished only by the reassembly alternative being a `PRE` form — `parse_script.py` reports these separately as "rules containing a PRE alternative (R5): `[\"YOU'RE\", \"I'M\"]`" (2 rules, 2 total `pre`-kind alternatives, `profile.txt`) |
| **R6** — `MEMORY`, pre-record a response for later | `(MEMORY keyword (decomp = reassembly) x4)` | `(MEMORY MY (0 YOUR 0 = LETS DISCUSS FURTHER WHY YOUR 3) ...)` | `1966_CACM_script.txt:120-131`, cited as "page 41 (f)" | Exactly 1 `MEMORY` rule in the script, target keyword `MY`, 4 sub-rules, each `0 YOUR 0` decomposing and a distinct reassembly — `1966_CACM_script.txt:225-229`; `profile.txt` "MEMORY MY: 4 sub-rules" |
| **NONE** — fallback when no keyword matched | Same shape as R1, keyword literally `NONE` | `(NONE ((0) (I AM NOT SURE I UNDERSTAND YOU FULLY) (PLEASE GO ON) (WHAT DOES THAT SUGGEST TO YOU) (DO YOU FEEL STRONGLY ABOUT DISCUSSING SUCH THINGS)))` | `1966_CACM_script.txt:134-147`, cited as "page 41 (d)"; the real `NONE` rule is at `:231-236` and is a verbatim match to the header's own worked example | Exactly 1 `NONE` rule found — `profile.txt` "NONE rules found: 1 (grammar requires exactly 1)"; 4 reassembly alternatives, all plain word lists |

## Decomposition pattern anatomy (inside R1/R5/NONE rule groups)

| Element | Meaning | Evidence |
|---|---|---|
| `0` | Zero-or-more wildcard segment | `1966_CACM_script.txt:54-55`; 98 occurrences total (`profile.txt`) |
| Literal word, e.g. `YOU`, `REMEMBER` | Must match that exact word at this position | e.g. `(0 YOU REMEMBER 0)` at `1966_CACM_script.txt:170` |
| `(/TAG ...)` | Matches one word carrying `TAG` (assigned via some `DLIST` rule elsewhere) | `1966_CACM_script.txt:452` `(0 YOUR 0 (/FAMILY) 0)`; 3 occurrences (`profile.txt`) |
| `(*WORD WORD ...)` | Matches one word that is literally one of the listed alternatives | `1966_CACM_script.txt:357` `(0 YOU (* WANT NEED) 0)`; 6 occurrences (`profile.txt`). HYPOTHESIS on exact meaning, see lexical table above — no prose definition exists in this file, only usage |

## Reassembly rule anatomy

| Element | Meaning | Evidence |
|---|---|---|
| Literal word | Emitted verbatim in the output | e.g. `TELL ME MORE ABOUT YOUR FAMILY` at `1966_CACM_script.txt:74` (header example) |
| Digit, e.g. `3`, `4`, `5` | Backreference: "Numbers in the reassembly rules refer to the parts of the decomposition rule match" | `1966_CACM_script.txt:56-60`, with the worked numeric example there (`(0 IF 0)` on "WHAT IF YOU DIE" gives `1`="WHAT", `2`="IF", `3`="YOU DIE") |
| `(=TARGET)` as a whole reassembly alternative | Hands processing off to another keyword's rules instead of emitting text | `1966_CACM_script.txt:100-107` (R4 grammar; the same `(=X)` shape used standalone as R4 also appears *inside* an R1 rule's list of reassembly alternatives, e.g. `DREAMT`'s 4th alternative `(=DREAM)` at `1966_CACM_script.txt:199`). `profile.txt`: 13 such `link`-kind alternatives found inside R1/NONE rule groups (separate from the 19 whole-rule R4 links above) |
| `(NEWKEY)` | "if there is more than one reassembly rule they are used in turn"; the header's R1 example uses `(NEWKEY)` as a catch-all last alternative | `1966_CACM_script.txt:80-81` (header example); 5 occurrences in the real script (`profile.txt` "newkey": 5), e.g. `1966_CACM_script.txt:184`, `:200`, `:210`, `:331`, `:538`. HYPOTHESIS on runtime meaning: the header never states in prose what selecting `(NEWKEY)` *does* (nothing in `:31-150` defines it), and Chapter I's `EXPEDITION.md` already recorded, independently, that the word `NEWKEY` is **not implemented as a control-flow construct anywhere in `MAD-SLIP_transcription.txt`** (`grep -n NEWKEY` there returns zero matches outside script data) — so whatever `(NEWKEY)` was meant to do (most likely: retry with the next-highest-precedence keyword, per Weizenbaum's prose, per `EXPEDITION.md` line 78-87) is not confirmed by any file at this dig site. I mark it HYPOTHESIS rather than fact for that reason. |
| `(PRE (reassembly) (=class))` | R5's pre-transform-then-link form, used as a reassembly alternative | `1966_CACM_script.txt:110-117`; both real occurrences: `YOU'RE` at `:336-338`, `I'M` at `:340-342` |

## `MEMORY` sub-rule anatomy

Unlike an R1 rule group (which nests decomposition and reassembly as separate
sibling lists), each `MEMORY` sub-rule is a single **flat** list containing
the decomposition words, then the literal atom `=`, then the reassembly
words, all in one list — confirmed by parsing `1966_CACM_script.txt:226`
(`(0 YOUR 0 = LETS DISCUSS FURTHER WHY YOUR 3)`) and finding the token `=`
inside that one list rather than as a separator between two sibling lists.
All 4 real sub-rules share the same decomposition, `(0 YOUR 0)`, differing
only in their reassembly text (`1966_CACM_script.txt:225-229`; verified by
inspecting the parsed structure directly, not just the profiler counts).

HYPOTHESIS: the header states `MEMORY` rules "pre-record responses for
later use" (`1966_CACM_script.txt:120`) but never says here, in this file,
*when* a memory is recorded, *when* it is played back, or how one of the
four sub-rules is chosen over another. `EXPEDITION.md` (Chapter I) already
flagged that the annotated transcription's claim of a deterministic `HASH`-
based selection (rather than Weizenbaum's stated "random") could not be
verified at this dig site — that remains an open Hypothesis from Chapter I,
not something this chapter's script-only parse can resolve.

## Precedence numbers

A precedence is an integer atom appearing right after the keyword (or after
`= substitution` if present), used, per the header, to rank which matched
keyword's rules run first: "ELIZA tries to match the decomposition rules
... only for the highest ranked keyword found" (`1966_CACM_script.txt:47-49`).

| Evidence | Detail |
|---|---|
| 21 of 68 rules carry an explicit precedence | `profile.txt` "Keywords with an explicit precedence number: 21" |
| Distinct values used | `1, 2, 3, 4, 5, 10, 15, 50` (`profile.txt`) |
| Highest precedence | `50`, shared by `COMPUTER`, `MACHINE`, `MACHINES`, `COMPUTERS` (`profile.txt`) |
| Un-numbered keywords | HYPOTHESIS: the header never states an explicit default for a keyword with no precedence digit; I infer "precedence 0 / lowest" only from the worked example comparing `ALIKE` (stated precedence 10) against implicitly-unranked words, and from `EXPEDITION.md`'s Chapter I trace ("keyword `ALIKE` has explicit precedence 10 ... and out-ranks the unranked keyword `ARE`... implicit precedence 0") — that trace is itself marked as a hand-trace against the golden transcript, not a rule stated anywhere in this script file |

## Anomalies found only by running the parser (not visible from a plain read)

- **The `=` operator is spelled two ways in the same file.** Most link forms
  are glued with no space, `(=WHAT)`, `(=DIT)`, `(=DREAM)` (confirmed:
  `grep -no '(= *[A-Z]*' relic/1966_CACM_script.txt` finds ~20 glued
  instances). Three are spaced, `(= EVERYONE)` at `1966_CACM_script.txt:523,
  524, 525` (`EVERYBODY`, `NOBODY`, `NOONE`). A tokenizer that only splits
  on whitespace misses the glued form entirely; the first version of
  `parse_script.py` did exactly that and silently misclassified 16 R4-link
  rules as malformed R1 rules until this was caught by cross-checking the
  reassembly-alternative counts against a hand grep — see the tokenizer
  comment in `parse_script.py` for the fix.
- **The keyword `MY` appears twice at the top level**, once as the target of
  `MEMORY MY` (`1966_CACM_script.txt:225`) and once as its own full
  transformation rule (`(MY = YOUR 2 ...)` at `:451-461`). `profile.txt`
  flags this: "Keywords appearing more than once at top level: ['MY']".
  HYPOTHESIS: this looks like two different things intentionally sharing a
  name (a memory *target* keyword vs. an actual rule keyword) rather than a
  transcription error, because both are separately documented in the header
  grammar (R1 and R6 are distinct forms) — but nothing in this file states
  outright that this duplication is intentional.
- **The header's R1 worked example (`1966_CACM_script.txt:72-81`) is not
  byte-identical to the real `MY` rule later in the file (`:451-461`).**
  The header example's first decomposition group ends with reassembly
  alternatives `(=WHAT)` and `(WHAT ELSE COMES TO MIND...)`; the real rule's
  first group instead has `(YOUR 4)` in place of `(=WHAT)` before the same
  final alternative. This is why the "R4-link inside a reassembly list"
  count above (13) comes entirely from *other* keywords (`DREAMT`,
  `REMEMBER`, `AM`, `ARE`, `WAS`, `CAN`, `WHY`, `LIKE`, `YOU`) rather than
  from `MY` — I checked this directly rather than assuming the header
  example and the real rule always match.

## Not determined at this dig site

- Whether `START`, `(NEWKEY)`, and the closing `()` have runtime meaning
  beyond what this static parse can show — this chapter parses the *script
  as data*, and none of these three constructs' actual effects are stated
  in this file's prose (see individual HYPOTHESIS notes above). `EXPEDITION.md`
  (Chapter I) already found that no MAD-SLIP compiler is available here to
  test them by running the program.
- Whether the 16-occurrence-vs-3-occurrence spacing split of `=` (glued vs.
  spaced) is meaningful (e.g. a second transcription pass) or arbitrary —
  nothing in the header's transcription notes (`:19-28`) mentions it.
