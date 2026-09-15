#!/usr/bin/env python3
"""parse_script.py -- read the ELIZA/DOCTOR script (1966 CACM appendix,
Anthony Hay's transcription), then let the DATA testify.

The script is a series of S-expressions: a greeting message, a bare atom
START, a set of keyword transformation rules (forms R1-R6 as documented in
the script's own header comment, 1966_CACM_script.txt:63-150), and a final
empty list (). This module parses the whole thing into a plain Python
structure with no knowledge of ELIZA semantics baked in beyond what the
header comment states, then reports counts of every construct found.

Usage: parse_script.py SCRIPT_FILE
"""
import re
import sys
from collections import Counter


# ---------------------------------------------------------------------------
# Tokenizer / S-expression parser
# ---------------------------------------------------------------------------

def strip_comments(text):
    """Drop any line whose first non-whitespace character is ';'.

    Evidence: every comment line in 1966_CACM_script.txt (the header block,
    lines 1-38, and the inline transcriber notes at lines 192, 252, 322,
    376, 428, 501, 508-509, 553) begins with ';' in column 0 with no leading
    whitespace -- verified by `sed -n '<line>p' | cat -A` during profiling.
    """
    kept = []
    for line in text.splitlines():
        if line.lstrip().startswith(";"):
            continue
        kept.append(line)
    return "\n".join(kept)


def tokenize(text):
    """Split into '(', ')', '=', and atom tokens.

    Parens are boundaries even with no surrounding whitespace: the script
    writes 'DLIST(/BELIEF)' with DLIST directly against '(' (no space), so
    a paren always closes the current atom, whitespace or not.

    '=' is also always its own token, for the same reason: the script is
    inconsistent about spacing it -- most equivalence-class links are
    glued, '(=WHAT)', '(=DIT)', but '(= EVERYONE)' (3x, keywords EVERYBODY/
    NOBODY/NOONE) has a space. Splitting '=' out unconditionally, the way
    '(' and ')' already are, handles both spellings identically. Evidence:
    `grep -no '(= *[A-Z]*' 1966_CACM_script.txt` shows 3 spaced instances
    against ~20+ glued ones; '=' never otherwise appears inside a word in
    this file (no contraction or literal uses it).
    """
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


class SExprParser:
    """Recursive-descent parser over the flat token stream.

    A parsed list is a Python list; a parsed atom is a Python str; a bare
    top-level atom (only 'START' in this script) is returned as a str, not
    wrapped in a list.
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse_top_level(self):
        forms = []
        while self.pos < len(self.tokens):
            forms.append(self.parse_one())
        return forms

    def parse_one(self):
        tok = self.tokens[self.pos]
        if tok == "(":
            return self.parse_list()
        if tok == ")":
            raise ValueError(f"unmatched ')' at token {self.pos}")
        self.pos += 1
        return tok

    def parse_list(self):
        assert self.tokens[self.pos] == "("
        self.pos += 1
        items = []
        while True:
            if self.pos >= len(self.tokens):
                raise ValueError("unexpected end of input inside a list")
            if self.tokens[self.pos] == ")":
                self.pos += 1
                return items
            items.append(self.parse_one())


def parse_script(path):
    with open(path) as f:
        raw = f.read()
    code = strip_comments(raw)
    tokens = tokenize(code)
    return SExprParser(tokens).parse_top_level()


# ---------------------------------------------------------------------------
# Classification of the top-level forms into the rule grammar the script's
# own header documents (1966_CACM_script.txt:63-150, forms R1-R6 + NONE).
# ---------------------------------------------------------------------------

def is_int_atom(tok):
    return isinstance(tok, str) and re.fullmatch(r"-?\d+", tok) is not None


def parse_dlist_tags(taglist):
    """taglist is the parsed contents of e.g. (/BELIEF), (/ FAMILY),
    (/NOUN FAMILY) -- three spacing variants seen in the script for the
    same DLIST(...) construct. A leading '/' may be glued to the first tag
    or stand alone as its own token; strip it either way."""
    if not taglist:
        return []
    first = taglist[0]
    rest = taglist[1:]
    if first.startswith("/"):
        stripped = first[1:]
        tags = ([stripped] if stripped else []) + list(rest)
    else:
        tags = list(taglist)
    return tags


def classify_reassembly_alt(alt):
    """One element of a reassembly list. alt is always a parsed list here."""
    if not alt:
        return {"kind": "empty"}
    if alt[0] == "=":
        return {"kind": "link", "target": alt[1] if len(alt) > 1 else None}
    if alt[0] == "NEWKEY":
        return {"kind": "newkey"}
    if alt[0] == "PRE":
        # R5: (PRE (reassembly_rule) (=equivalence_class))
        pre_reassembly = alt[1] if len(alt) > 1 else None
        link = None
        if len(alt) > 2 and isinstance(alt[2], list) and alt[2] and alt[2][0] == "=":
            link = alt[2][1] if len(alt[2]) > 1 else None
        return {"kind": "pre", "reassembly": pre_reassembly, "link": link}
    return {"kind": "words", "words": alt}


def classify_decomposition(pattern):
    """Count the special tokens inside a decomposition pattern: '0'
    (zero-or-more wildcard), other digits (unused in decomposition, only
    meaningful in reassembly, but recorded if seen), (/TAG) tag-match
    sublists, (*WORD WORD) word-class sublists, and plain literal words."""
    info = {"zero_wildcards": 0, "tag_matches": [], "class_matches": [], "literals": []}
    for item in pattern:
        if item == "0":
            info["zero_wildcards"] += 1
        elif isinstance(item, list):
            if item and isinstance(item[0], str) and item[0].startswith("/"):
                info["tag_matches"].append(parse_dlist_tags(item))
            elif item and isinstance(item[0], str) and item[0].startswith("*"):
                first = item[0][1:]
                words = ([first] if first else []) + list(item[1:])
                info["class_matches"].append(words)
            else:
                info["literals"].append(item)  # unexpected nested form
        else:
            info["literals"].append(item)
    return info


def classify_keyword_rule(elements):
    """elements is the parsed contents of one top-level keyword form, e.g.
    ['MY', '=', 'YOUR', '2', [[...decomp...], [...reassembly...], ...]].
    Returns a dict describing keyword, substitution, precedence, and body.
    """
    keyword = elements[0]
    idx = 1
    substitution = None
    if idx < len(elements) and elements[idx] == "=":
        substitution = elements[idx + 1] if idx + 1 < len(elements) else None
        idx += 2
    precedence = None
    if idx < len(elements) and is_int_atom(elements[idx]):
        precedence = int(elements[idx])
        idx += 1
    body = elements[idx:]

    rule = {
        "keyword": keyword,
        "substitution": substitution,
        "precedence": precedence,
        "form": None,
        "dlist_tags": None,
        "link_target": None,
        "rule_groups": None,
    }

    if keyword == "MEMORY":
        rule["form"] = "R6-MEMORY"
        # elements: ['MEMORY', memory_keyword, sub1, sub2, sub3, sub4]
        rule["keyword"] = elements[1]
        rule["memory_subrules"] = []
        for sub in elements[2:]:
            if "=" in sub:
                eq = sub.index("=")
                decomp, reassembly = sub[:eq], sub[eq + 1:]
            else:
                decomp, reassembly = sub, []
            rule["memory_subrules"].append({"decomposition": decomp, "reassembly": reassembly})
        return rule

    if len(body) == 0:
        rule["form"] = "R2-substitution" if substitution is not None else "R0-bare"
        return rule

    if body[0] == "DLIST":
        rule["form"] = "R3-DLIST"
        taglist = body[1] if len(body) > 1 and isinstance(body[1], list) else []
        rule["dlist_tags"] = parse_dlist_tags(taglist)
        return rule

    if len(body) == 1 and isinstance(body[0], list) and body[0][:1] == ["="]:
        rule["form"] = "R4-link"
        rule["link_target"] = body[0][1] if len(body[0]) > 1 else None
        return rule

    # Otherwise: one or more (decomposition reassembly reassembly ...) groups.
    # A group whose sole reassembly is (PRE ...) is documented as R5; we
    # still record it as a rule_group and flag the PRE alt's kind below, so
    # a rule with only PRE alts is distinguishable from a plain R1 rule.
    rule["form"] = "R1/R5-decomposition" if keyword != "NONE" else "NONE"
    groups = []
    for group in body:
        if not isinstance(group, list) or not group:
            continue
        decomposition = group[0]
        alts_raw = group[1:]
        alts = [classify_reassembly_alt(a) for a in alts_raw]
        groups.append({
            "decomposition": decomposition,
            "decomposition_info": classify_decomposition(decomposition) if isinstance(decomposition, list) else None,
            "reassembly_alts": alts,
        })
    rule["rule_groups"] = groups
    return rule


def parse_full(path):
    """Top-level: greeting message, bare atom START, keyword rules, final ()."""
    forms = parse_script(path)
    if len(forms) < 3:
        raise ValueError(f"expected at least 3 top-level forms, got {len(forms)}")

    greeting = forms[0]
    if not isinstance(greeting, list):
        raise ValueError("expected the first top-level form to be the greeting list")

    if forms[1] != "START":
        raise ValueError(f"expected the second top-level form to be bare atom START, got {forms[1]!r}")

    if forms[-1] != []:
        raise ValueError(f"expected the last top-level form to be an empty list (), got {forms[-1]!r}")

    keyword_forms = forms[2:-1]
    rules = []
    for elements in keyword_forms:
        if not isinstance(elements, list) or not elements:
            raise ValueError(f"expected a nonempty keyword rule list, got {elements!r}")
        rules.append(classify_keyword_rule(elements))

    return {"greeting": greeting, "rules": rules}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(parsed):
    rules = parsed["rules"]
    lines = []
    lines.append(f"Greeting: {' '.join(parsed['greeting'])!r}")
    lines.append(f"Top-level keyword/MEMORY/NONE forms: {len(rules)}")
    lines.append("")

    form_counts = Counter(r["form"] for r in rules)
    lines.append("Rules by form:")
    for form, n in sorted(form_counts.items()):
        lines.append(f"  {form:<20} {n}")
    lines.append("")

    with_sub = [r for r in rules if r["substitution"] is not None]
    lines.append(f"Keywords with a '=' substitution: {len(with_sub)}")
    for r in with_sub:
        lines.append(f"  {r['keyword']} = {r['substitution']}")
    lines.append("")

    with_prec = [r for r in rules if r["precedence"] is not None]
    lines.append(f"Keywords with an explicit precedence number: {len(with_prec)}")
    prec_vals = sorted({r["precedence"] for r in with_prec})
    lines.append(f"  distinct precedence values seen: {prec_vals}")
    for r in sorted(with_prec, key=lambda r: -r["precedence"]):
        lines.append(f"  {r['keyword']:<12} precedence {r['precedence']}")
    lines.append("")

    dlist_rules = [r for r in rules if r["form"] == "R3-DLIST"]
    lines.append(f"DLIST tag rules (R3): {len(dlist_rules)}")
    tag_counter = Counter()
    for r in dlist_rules:
        tag_counter.update(r["dlist_tags"])
        lines.append(f"  {r['keyword']:<12} tags={r['dlist_tags']}")
    lines.append(f"  distinct tags used: {dict(tag_counter)}")
    lines.append("")

    link_rules = [r for r in rules if r["form"] == "R4-link"]
    lines.append(f"Pure link/equivalence rules (R4, e.g. (HOW (=WHAT))): {len(link_rules)}")
    for r in link_rules:
        lines.append(f"  {r['keyword']:<12} -> (={r['link_target']})")
    lines.append("")

    memory_rules = [r for r in rules if r["form"] == "R6-MEMORY"]
    lines.append(f"MEMORY rules (R6): {len(memory_rules)}")
    for r in memory_rules:
        lines.append(f"  MEMORY {r['keyword']}: {len(r['memory_subrules'])} sub-rules")
    lines.append("")

    none_rules = [r for r in rules if r["form"] == "NONE"]
    lines.append(f"NONE rules found: {len(none_rules)} (grammar requires exactly 1)")

    decomp_rules = [r for r in rules if r["form"] == "R1/R5-decomposition"]
    total_groups = sum(len(r["rule_groups"]) for r in decomp_rules)
    total_alts = sum(len(g["reassembly_alts"]) for r in decomp_rules for g in r["rule_groups"])
    lines.append(f"Decomposition rules (R1/R5, keyword != NONE): {len(decomp_rules)}")
    lines.append(f"  total decomposition-pattern groups: {total_groups}")
    lines.append(f"  total reassembly alternatives across all groups: {total_alts}")

    alt_kind_counts = Counter()
    for r in decomp_rules + none_rules:
        for g in r["rule_groups"]:
            for a in g["reassembly_alts"]:
                alt_kind_counts[a["kind"]] += 1
    lines.append(f"  reassembly alternative kinds (incl. NONE): {dict(alt_kind_counts)}")

    pre_rules = []
    for r in decomp_rules:
        for g in r["rule_groups"]:
            if any(a["kind"] == "pre" for a in g["reassembly_alts"]):
                pre_rules.append(r["keyword"])
    lines.append(f"  rules containing a PRE alternative (R5): {pre_rules}")

    zero_wc = 0
    tag_match_count = 0
    class_match_count = 0
    for r in decomp_rules + none_rules:
        for g in r["rule_groups"]:
            info = g["decomposition_info"]
            if info:
                zero_wc += info["zero_wildcards"]
                tag_match_count += len(info["tag_matches"])
                class_match_count += len(info["class_matches"])
    lines.append(f"  total '0' zero-or-more wildcards across all decomposition patterns: {zero_wc}")
    lines.append(f"  decomposition patterns using a (/TAG) tag-match: {tag_match_count}")
    lines.append(f"  decomposition patterns using a (*WORD ...) class-match: {class_match_count}")
    lines.append("")

    all_keywords = [r["keyword"] for r in rules]
    dup_keywords = [k for k, n in Counter(all_keywords).items() if n > 1]
    lines.append(f"Total distinct top-level keywords (incl. the MEMORY target keyword): {len(set(all_keywords))}")
    lines.append(f"Keywords appearing more than once at top level: {dup_keywords}")

    return "\n".join(lines)


def main(argv):
    if len(argv) != 2:
        print(f"usage: {argv[0]} SCRIPT_FILE", file=sys.stderr)
        return 2
    parsed = parse_full(argv[1])
    print(report(parsed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
