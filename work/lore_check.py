#!/usr/bin/env python3
"""lore_check.py — every decision record must carry its evidence.

Checks each lore/ADR-*.md for the five required sections. Exit 1 on any gap.
"""
import glob
import re
import sys

REQUIRED = ("Status", "Context", "Decision", "Evidence", "Consequences")

def main():
    problems = 0
    files = sorted(glob.glob("lore/ADR-*.md"))
    if not files:
        print("no ADRs found under lore/ — the Lore is empty")
        return 1
    for path in files:
        text = open(path).read()
        headings = set(re.findall(r"^## (\w+)", text, re.M))
        missing = [s for s in REQUIRED if s not in headings]

        # Count evidence bullet points
        if "## Evidence" in text:
            evidence_section = text.split("## Evidence")[1]
            if len(evidence_section.split("## ")) > 1:
                evidence_section = evidence_section.split("## ")[0]
            cites = len(re.findall(r"^- ", evidence_section, re.M))
        else:
            cites = 0

        status = "ok" if not missing and cites else "INCOMPLETE"
        problems += status != "ok"

        msg = f"{path}: {status}"
        if missing:
            msg += f" — missing {missing}"
        if cites:
            msg += f" — {cites} evidence item(s)"
        else:
            msg += " — Evidence lists nothing"

        print(msg)

    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())
