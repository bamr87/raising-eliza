# ELIZA Modernization Roadmap

This roadmap separates the ideas that drive ELIZA from the housing that happens to implement them. An idea stays because it is right; housing changes when the implementation is no longer fitting. Dated deferrals mark decisions that await future facts.

| Element | Verdict | Why |
|---------|---------|-----|
| **Core algorithm: keyword ranking by precedence** | **Stays** — an idea | Ranking keywords by precedence (not first-match) is the core insight that makes ELIZA respond contextually. The precedence numbers are data; reprioritizing them changes behavior but does not break the algorithm. |
| **Six rule forms: R1–R6 decomposition and reassembly** | **Stays** — an idea | The script's grammar (six decomposition patterns, reassembly rule cycling) is what makes scripting DOCTOR easy. These patterns are independent of MAD-SLIP syntax. ADR-0001: the transcription with disclosed corrections is accepted. |
| **Keyword substitution ("=") applied in-place** | **Stays** — an idea | Converting "remember" to "recall" before keyword matching is a clever data-driven personalization; the mechanism is architecture-independent. Eliza.py reproduces this; a future port to another language should too. |
| **Clause delimiters (`.`, `,`, `BUT`)** | **Stays** — an idea | Breaking the input into clauses and matching keywords clause-by-clause (rather than sentence-wide) is a linguistic insight Weizenbaum built in. It improves contextual replies. The delimiters are data; changing them requires only script updates. |
| **MEMORY: capture and recall** | **Stays** — an idea | Remembering facts the user disclosed and echoing them back later is the primary mechanism that makes ELIZA feel like it understands. The FIFO queue and the recall condition (every four turns without keyword) are documented. |
| **MEMORY slot assignment via HASH** | **Changes** — housing | ADR-0003: The original SLIP HASH algorithm cannot be run (SLIP not available, not documented). The port uses a deterministic backward cycle instead. This is a reconstruction, correct only for the golden transcript, not a proven-equivalent replacement. Once a MAD-SLIP compiler is available, the original can be run and compared. |
| **NEWKEY retry functionality** | **Changes** — housing | ADR-0002: The transcribed MAD-SLIP code does not implement NEWKEY as a retry; it prints the literal string. This is a known architectural reduction. A future port should replicate it (to match the transcript) or implement Weizenbaum's intended retry (to match the 1966 paper), but not attempt a guess. The golden transcript does not exercise this; new inputs might. |
| **MAD-SLIP language** | **Changes** — housing | Python is more portable, more readable, and has a large interpreter base. MAD-SLIP is extinct and no longer serves the algorithm. The port's logic is faithful; the language is not. |
| **IBM 7094 era data structures (SLIP vectors, SLIP lists)** | **Changes** — housing | Python dicts, lists, and strings handle memory management and data organization. The functional equivalents are chosen for clarity and performance, not literal byte-for-byte replication. Eliza.py documents which parts are reconstructed (MEMORY hash, NOMATCH fillers). |
| **Batch processing (fixed input file, written output)** | **Changes** — housing | The gate (eliza_gate.py) provides request/reply HTTP routing instead of reading an input file and writing an output file. The algorithm is unchanged; the I/O model is appropriate to modern use. The port can be called interactively (python3 eliza.py) or via the gate. |
| **Interactive single-session mode** | **Stays** — housing | The port supports interactive prompt for testing and learning. No production use requires this, but it is invaluable for debugging and demonstration. Keep it. |
| **Gate's three-engine design: replay, shadow, live** | **Stays** — housing | ADR-0004 documents this as a safe-cutover pattern. Replay mode is the closest thing to running the original relic; shadow mode proves the port is equal; live mode runs the port in production. The design is proven and minimal. |
| **HTTP routing (instead of file I/O)** | **Stays** — housing | Modern services use HTTP. The gate speaks HTTP. The algorithm is unchanged; the boundary is appropriate. |
| **Per-conversation state in memory (within one process)** | **Deferred** — scalability | The current gate keeps conversation state (MEMORY queue, reassembly cursors, replay cursor) in Python dicts, keyed by conversation_id. This works for single-process testing and small deployments. For horizontal scaling (multiple gate instances), state must move to a shared cache (Redis, etc.). Decision deferred: implement once deployment requirements are clear. No test currently requires this. |
| **Golden transcript as the source of truth** | **Stays** — an idea | The 15-turn transcript from the 1966 CACM paper is the only executable proof of what the relic does. The port is correct if and only if it reproduces this transcript. Characterization trials and the ledger validate against it. This is the right standard until a MAD-SLIP compiler appears. |

## Forward Compatibility and Dated Deferrals

### ADR-0005: When MAD-SLIP becomes available (review by 2050-01-01)

Once a MAD-SLIP compiler is available, the original relic can be run and compared against the port on:
- The golden transcript (to re-validate the 1966 paper's sample conversation)
- A new test corpus (to validate that MEMORY, NEWKEY, and other reconstructions are correct on new inputs)

If the relic's output matches the port's output on both, the port is promoted from "reconstruction" to "verified". If not, new ADRs must document the differences and decide: does the port need fixing, or was the reconstruction correct for our use case?

No ADRs are labeled "remove this and rebuild" — they are labeled "review by 2050" to ensure the decision is revisited if facts change.

## Decision Table Legend

- **Stays — an idea**: The concept is central to what ELIZA is. Change it only if you are changing what ELIZA does, not how it is housed.
- **Stays — housing**: The implementation detail is good enough and has no known issues. Keep it unless you know why it should change.
- **Changes — housing**: The original housing is no longer available or appropriate. A modern replacement is in place and validated. This is a decision, not a guess.
- **Deferred — dated**: A decision is waiting on external facts (availability of a compiler, scaling requirements, etc.). The deferral carries a review date; revisit it even if nothing has changed.

## How to Use This Roadmap

Before proposing a change to any part of ELIZA:
1. Find the element in this table.
2. Read the reason and any linked ADR.
3. If your change touches an idea, you are proposing to change what ELIZA does; make that case explicitly.
4. If your change touches housing, you are proposing a modernization; link to why the current housing is inadequate.
5. If your change touches a dated deferral, check the review date; if it has passed, re-open the ADR and decide.
