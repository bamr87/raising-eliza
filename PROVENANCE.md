# Provenance

Every claim on this page was verified against a file in `relic/` or in the upstream
repository, not from memory. Where I could not verify something, it says so.

## What the relic is

ELIZA, as Joseph Weizenbaum actually wrote it: in MAD-SLIP, for the Compatible
Time-Sharing System (CTSS) on an IBM 7094, at MIT in the mid-1960s.

This is not one of the hundreds of later ELIZA reimplementations. It is the original
program, and it had been out of circulation for roughly half a century before it was
found again in Weizenbaum's own papers.

## Chain of custody

| Link | What it is | How I verified it |
|---|---|---|
| MIT Libraries, Distinctive Collections | Collection **MC-0383, box 8**, folder labelled `COMPUTER CONVERSATIONS (1965)`, Joseph Weizenbaum personal archives | Read the scanned folder cover at `1965_Weizenbaum_MAD-SLIP/ORIGINAL_ELIZA_IN_MAD_SLIP_CC0_For_Resease.png` — the box, collection and repository are written on it by hand |
| Public-domain dedication | The same scan carries the **Public Domain** mark and the **Creative Commons Zero (CC0 1.0)** badge, with the `creativecommons.org/publicdomain/zero/1.0` URL | Read from the scan itself |
| Transcription to text | `MAD-SLIP_transcription.txt` — the card deck typed back in, punched-card sequence numbers intact in columns 73–80 (`000010`, `000020`, …) | Read the file; the sequence numbers are visible on every line |
| Second, independent transcription | `ELIZA_transcription_annotated_20220216.txt` — annotated, dated 2022-02-16 | Read the file |
| The DOCTOR script | `1966_CACM_script.txt` — the script appendix from Weizenbaum's January 1966 *Communications of the ACM* paper | Read the file |
| CTSS SLIP runtime | Separately deposited, `Copyright 1965 MIT`, MIT-licensed, from MIT DOME handle `1721.3/201707` | Read `1965_Weizenbaum_MAD-SLIP/Slip/CTSS/README.md` |
| Publication | `jeffshrager/elizagen.org` on GitHub, cloned at commit `9756f6d` | `git log` in the clone |

## What I did not verify

- The exact date and circumstances of the rediscovery. It is widely reported as 2021,
  and the upstream repository was reorganised on 2021-07-26, but I did not find a
  primary source for the discovery date among the files I read, so this repository
  does not assert one.
- Whether MAD enforces a six-character identifier limit. This matters because the two
  independent transcriptions disagree on three identifiers (`SUBJCT`/`SUBJECT`,
  `OBJCT`/`OBJECT`, and an `LNKL`/`LNKLL` typo). Resolving it needs the MAD manual,
  and the question is recorded as open rather than guessed at.

## Two licences, kept separate

- **The relic** (`relic/`) is CC0 / public domain, per the dedication above. It is
  reproduced here unchanged.
- **Everything this project wrote** — the port, the trials, the ledger, the gate, the
  harness, this documentation — is MIT-licensed. See `LICENSE`.

Nothing here claims authorship of Weizenbaum's work. The port is a new implementation
that reproduces the behaviour of his program, driven by his script as data.

## The condition of the dig

There is no working MAD-SLIP compiler. The original program therefore **cannot be run**
to check anything against. That is the defining constraint of this whole exercise, and
it is why the golden master matters: the fifteen-turn conversation Weizenbaum published
in the 1966 CACM paper is the only observable output of the original system that
survives. It is the sole oracle. Everything else is reading.
