#!/usr/bin/env python3
"""eliza.py -- a faithful port of Weizenbaum's 1966 DOCTOR/ELIZA.

This module parses relic/1966_CACM_script.txt (Anthony Hay's transcription
of the script appendix to Weizenbaum's January 1966 CACM article) as DATA,
using the grammar the script's own header comment documents (six rule forms
R1-R6 plus NONE, 1966_CACM_script.txt:63-150), and runs the algorithm that
header describes: keyword ranking by precedence, decomposition matching
with '0' wildcards / (/TAG) tag-matches / (*WORD...) class-matches,
reassembly rules cycled in turn per decomposition group, keyword
substitution and equivalence-class links, the MEMORY mechanism, and the
NONE fallback. Nothing about DOCTOR's specific conversation is hardcoded
here; every reply is produced by matching and reassembling against rules
read from the script file at import/construction time.

Sources for the pieces the header leaves undocumented (verified against
MAD-SLIP_transcription.txt, the ELIZA main routine, since no MAD-SLIP
compiler is available to run it -- see work/EXPEDITION.md):

  - Keyword substitution ("=") is applied in place, to every scanned word
    that names a substituting rule, whether or not that word ends up being
    the turn's chosen keyword (MAD-SLIP_transcription.txt TESTS function,
    the SUBST/INSRT branch; hand-verified against golden turns 3, 11, 21).
  - '.', ',' and the literal word BUT are clause delimiters: hit before any
    keyword is found, the words so far are discarded and scanning resumes;
    hit after a keyword is found, scanning stops there and the remainder is
    discarded (ELIZA main loop, MAD-SLIP_transcription.txt:280-292; verified
    against golden turns 3, 5, 21).
  - Each decomposition group's reassembly list is used "in turn on
    successive matches" (the header's own words, 1966_CACM_script.txt:52):
    one next-index counter per (keyword, group), advancing every time that
    group is chosen, wrapping to 0 after the last alternative. Verified
    against golden turns 13/15/17/27 (MY's family-tagged group, used four
    times) and turns 1/19 (DIT's group, reached via two different keywords).
  - (NEWKEY) is not implemented as control flow anywhere in
    MAD-SLIP_transcription.txt (grep finds zero matches outside script
    data); per work/DATA_DICTIONARY.md this is HYPOTHESIS-backed as "prints
    the literal word NEWKEY", which is what this port does. Not exercised
    by the golden transcript.
  - MEMORY: whenever the MEMORY-designated keyword (MY) is the turn's
    chosen keyword, a memory is built from the fixed (0 YOUR 0) pattern
    against that turn's substituted sentence and queued (FIFO -- Weizenbaum
    1966 describes memories as replayed oldest-first). Recall happens only
    when no keyword is found AND a MAD-style turn counter that cycles
    1,2,3,4,1,2,... lands on 4 (MAD-SLIP_transcription.txt LIMIT variable;
    verified: golden's only no-keyword turn is turn 15, and 15 is the 15th
    input, landing on LIMIT==4 under that exact recurrence). The MAD source
    picks which of the four memory templates to file a memory under via
    HASH.(BOT.(INPUT),2)+1 -- a SLIP library primitive whose algorithm is
    not present at this dig site (work/EXPEDITION.md "Hypotheses"), so it
    cannot be reproduced bit for bit. This port uses its own deterministic,
    content-independent stand-in -- a per-keyword counter dedicated to
    MEMORY that starts at the last template and cycles backward
    (3,2,1,0,3,2,1,0,...) -- documented here as a reconstruction, not a
    recovered fact: it is what reproduces the transcript's one memory
    recall (turn 30, filed at turn 5) and has not been exercised against
    any second memory recall because the golden transcript contains only
    one.
  - When a keyword is found but none of its (or a linked keyword's)
    decomposition groups match, or link-chasing runs out, the MAD source
    prints one of four fixed fillers indexed by the same turn counter
    (NOMATCH(1..4), MAD-SLIP_transcription.txt:429-436). Implemented for
    completeness; not exercised by the golden transcript.

Usage:
    eliza = Eliza()                  # loads the default script path
    eliza.respond("Men are all alike.")   # -> "IN WHAT WAY"
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCRIPT_PATH = os.path.join(HERE, "..", "relic", "1966_CACM_script.txt")

DELIMITERS = {".", ",", "BUT"}
NOMATCH_FILLERS = ["PLEASE CONTINUE", "HMMM", "GO ON, PLEASE", "I SEE"]


# ---------------------------------------------------------------------------
# Parsing the script into a runtime rule table (the script as DATA)
# ---------------------------------------------------------------------------

def _strip_comments(text):
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(";")
    )


def _tokenize(text):
    tokens = []
    buf = []

    def flush():
        if buf:
            tokens.append("".join(buf))
            buf.clear()

    for ch in text:
        if ch in "()=":
            flush()
            tokens.append(ch)
        elif ch.isspace():
            flush()
        else:
            buf.append(ch)
    flush()
    return tokens


class _SExprParser:
    """Recursive-descent reader for the script's S-expressions."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse_top_level(self):
        forms = []
        while self.pos < len(self.tokens):
            forms.append(self._parse_one())
        return forms

    def _parse_one(self):
        tok = self.tokens[self.pos]
        if tok == "(":
            return self._parse_list()
        if tok == ")":
            raise ValueError(f"unmatched ')' at token {self.pos}")
        self.pos += 1
        return tok

    def _parse_list(self):
        self.pos += 1  # consume '('
        items = []
        while True:
            if self.pos >= len(self.tokens):
                raise ValueError("unexpected end of input inside a list")
            if self.tokens[self.pos] == ")":
                self.pos += 1
                return items
            items.append(self._parse_one())


def _is_int_atom(tok):
    return isinstance(tok, str) and re.fullmatch(r"-?\d+", tok) is not None


def _dlist_tags(taglist):
    """taglist is the parsed contents of e.g. (/BELIEF), (/ FAMILY),
    (/NOUN FAMILY): a leading '/' may be glued to the first tag or stand
    alone as its own token."""
    if not taglist:
        return set()
    first, rest = taglist[0], taglist[1:]
    if first.startswith("/"):
        stripped = first[1:]
        return set(([stripped] if stripped else []) + list(rest))
    return set(taglist)


class _Pattern:
    """One compiled decomposition-pattern element."""

    __slots__ = ("kind", "value")

    def __init__(self, kind, value=None):
        self.kind = kind      # "wild" | "lit" | "tag" | "class"
        self.value = value


def _compile_decomposition(pattern_items):
    compiled = []
    for item in pattern_items:
        if item == "0":
            compiled.append(_Pattern("wild"))
        elif isinstance(item, list):
            if item and isinstance(item[0], str) and item[0].startswith("/"):
                compiled.append(_Pattern("tag", _dlist_tags(item)))
            elif item and isinstance(item[0], str) and item[0].startswith("*"):
                first = item[0][1:]
                words = set(([first] if first else []) + list(item[1:]))
                compiled.append(_Pattern("class", words))
            else:
                raise ValueError(f"unrecognised decomposition element {item!r}")
        else:
            compiled.append(_Pattern("lit", item))
    return compiled


def _classify_reassembly_alt(alt):
    if not alt:
        return {"kind": "words", "words": []}
    if alt[0] == "=":
        return {"kind": "link", "target": alt[1]}
    if alt[0] == "NEWKEY":
        return {"kind": "newkey"}
    if alt[0] == "PRE":
        pre_words = alt[1]
        link = alt[2][1] if len(alt) > 2 and isinstance(alt[2], list) else None
        return {"kind": "pre", "words": pre_words, "target": link}
    return {"kind": "words", "words": alt}


class Script:
    """The parsed rule table: everything eliza.py knows comes from here."""

    def __init__(self, path):
        self.substitutions = {}     # WORD -> [replacement words]
        self.precedence = {}        # WORD -> int
        self.tags = {}              # WORD -> set(tags)
        self.rules = {}             # WORD -> {"groups": [...]} or {"link": TARGET}
        self.memory_keyword = None
        self.memory_subrules = []   # [{"pattern": [...], "reassembly": [...]}]
        self.greeting = []
        self._load(path)

    def _load(self, path):
        with open(path) as f:
            raw = f.read()
        forms = _SExprParser(_tokenize(_strip_comments(raw))).parse_top_level()
        if len(forms) < 3 or forms[1] != "START" or forms[-1] != []:
            raise ValueError("script does not have the expected shape: "
                              "greeting, START, keyword forms..., ()")
        self.greeting = forms[0]
        for elements in forms[2:-1]:
            self._add_rule(elements)

    def _add_rule(self, elements):
        keyword = elements[0]

        if keyword == "MEMORY":
            self.memory_keyword = elements[1]
            for sub in elements[2:]:
                eq = sub.index("=")
                self.memory_subrules.append({
                    "pattern": _compile_decomposition(sub[:eq]),
                    "reassembly": sub[eq + 1:],
                })
            return

        idx = 1
        if idx < len(elements) and elements[idx] == "=":
            self.substitutions[keyword] = [elements[idx + 1]]
            idx += 2
        if idx < len(elements) and _is_int_atom(elements[idx]):
            self.precedence[keyword] = int(elements[idx])
            idx += 1
        body = elements[idx:]

        if not body:
            return  # R2: substitution only, no decomposition/link

        if body[0] == "DLIST":
            taglist = body[1] if len(body) > 1 and isinstance(body[1], list) else []
            self.tags[keyword] = _dlist_tags(taglist)
            return

        if len(body) == 1 and isinstance(body[0], list) and body[0][:1] == ["="]:
            self.rules[keyword] = {"link": body[0][1]}
            return

        groups = []
        for group in body:
            decomposition, alts = group[0], group[1:]
            groups.append({
                "pattern": _compile_decomposition(decomposition),
                "alts": [_classify_reassembly_alt(a) for a in alts],
                "next_alt": 0,
            })
        self.rules[keyword] = {"groups": groups}


# ---------------------------------------------------------------------------
# Matching and reassembly
# ---------------------------------------------------------------------------

def _match(pattern, words, tags):
    """Try to match a compiled decomposition pattern against a word list.
    Returns a list of captured word-lists (one per pattern position, in
    order), or None. '0' tries the shortest expansion first, so the first
    literal anchor after a wildcard binds to its leftmost occurrence --
    matches the header's own worked example (0 IF 0) on "WHAT IF YOU DIE".
    `tags` is the script's WORD -> set(DLIST tags) table, for (/TAG)
    elements."""

    def rec(pi, wi):
        if pi == len(pattern):
            return [] if wi == len(words) else None
        elem = pattern[pi]
        if elem.kind == "wild":
            for take in range(0, len(words) - wi + 1):
                rest = rec(pi + 1, wi + take)
                if rest is not None:
                    return [words[wi:wi + take]] + rest
            return None
        if wi >= len(words):
            return None
        word = words[wi]
        if elem.kind == "lit":
            if word != elem.value:
                return None
        elif elem.kind == "tag":
            if not (tags.get(word, set()) & elem.value):
                return None
        elif elem.kind == "class":
            if word not in elem.value:
                return None
        rest = rec(pi + 1, wi + 1)
        return None if rest is None else [[word]] + rest

    return rec(0, 0)


def _assemble(words_template, captured):
    out = []
    for tok in words_template:
        if tok.isdigit():
            out.extend(captured[int(tok) - 1])
        else:
            out.append(tok)
    return out


# ---------------------------------------------------------------------------
# The conversational engine
# ---------------------------------------------------------------------------

class Eliza:
    def __init__(self, script_path=DEFAULT_SCRIPT_PATH):
        self.script = Script(script_path)
        self.memory_queue = []       # FIFO of already-assembled memory strings
        self.memory_next_template = 3  # reconstructed selector, see module docstring
        self.turn_count = 0

    def greeting_line(self):
        return " ".join(self.script.greeting)

    # -- turn processing ----------------------------------------------------

    def respond(self, text):
        self.turn_count += 1
        limit = (self.turn_count + 1) % 4 or 4

        keyword, sentence = self._scan(text)

        if keyword is None:
            if limit == 4 and self.memory_queue:
                return self.memory_queue.pop(0)
            return self._reassemble_from("NONE", [])

        if keyword == self.script.memory_keyword:
            self._store_memory(sentence)

        return self._reassemble_from(keyword, sentence)

    def _scan(self, text):
        """Tokenize, apply in-place substitution, rank keywords by
        precedence, and honour the '.', ',', BUT clause-delimiter rule."""
        tokens = re.findall(r"[A-Za-z']+|[.,]", text.upper())
        sentence = []
        best_keyword, best_precedence = None, None

        for tok in tokens:
            if tok in DELIMITERS:
                if best_keyword is None:
                    sentence = []
                    continue
                break

            rule = self.script.rules.get(tok)
            sub = self.script.substitutions.get(tok)
            sentence.extend(sub if sub else [tok])

            if rule is not None:
                precedence = self.script.precedence.get(tok, 0)
                if best_keyword is None or precedence > best_precedence:
                    best_keyword, best_precedence = tok, precedence

        return best_keyword, sentence

    # -- decomposition / reassembly / link-chasing --------------------------

    def _reassemble_from(self, keyword, sentence, depth=0):
        """Match `sentence` against `keyword`'s rule-groups (chasing plain
        R4 links first), apply the next reassembly alternative in that
        group's cycle, and return the resulting text. A (=TARGET) link
        alternative and an R4 link both re-run this against the SAME
        sentence; a PRE alternative re-runs it against newly generated
        text instead (1966_CACM_script.txt R4 vs R5, :100-117)."""
        if depth > 20:
            return NOMATCH_FILLERS[0]

        rule = self.script.rules.get(keyword)
        if rule is None:
            return NOMATCH_FILLERS[(self.turn_count - 1) % 4]

        if "link" in rule:
            return self._reassemble_from(rule["link"], sentence, depth + 1)

        for group in rule["groups"]:
            captured = _match(group["pattern"], sentence, self.script.tags)
            if captured is None:
                continue
            alt = group["alts"][group["next_alt"]]
            group["next_alt"] = (group["next_alt"] + 1) % len(group["alts"])
            return self._apply_alt(alt, sentence, captured, depth)

        return NOMATCH_FILLERS[(self.turn_count - 1) % 4]

    def _apply_alt(self, alt, sentence, captured, depth):
        if alt["kind"] == "words":
            return " ".join(_assemble(alt["words"], captured))
        if alt["kind"] == "newkey":
            return "NEWKEY"
        if alt["kind"] == "link":
            return self._reassemble_from(alt["target"], sentence, depth + 1)
        if alt["kind"] == "pre":
            new_sentence = _assemble(alt["words"], captured)
            return self._reassemble_from(alt["target"], new_sentence, depth + 1)
        raise ValueError(f"unknown reassembly alternative kind {alt!r}")

    # -- MEMORY ---------------------------------------------------------

    def _store_memory(self, sentence):
        subrule = self.script.memory_subrules[self.memory_next_template]
        self.memory_next_template = (self.memory_next_template - 1) % 4
        captured = _match(subrule["pattern"], sentence, self.script.tags)
        if captured is None:
            return
        text = " ".join(_assemble(subrule["reassembly"], captured))
        self.memory_queue.append(text)


if __name__ == "__main__":
    import sys

    eliza = Eliza()
    print(eliza.greeting_line())
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        print(eliza.respond(line))
