#!/usr/bin/env python3
"""Check that every guide tab-set has both language tabs.

Rules (see guide/grove/index.md for the layout):
  1. Every ``{tab-set}`` must contain exactly one ``{{ cpp_tab }}`` and one ``{{ py_tab }}`` tab.
  2. In pages converted to the per-section layout, Markdown headings must live outside the tabs
     (section heading, then one tab-set per section).

Usage: python3 tools/check_tab_parity.py [source_dir]   -> exit 1 on any violation
"""
import re
import sys
from pathlib import Path

# Pages already converted to "## heading outside, one tab-set per section". Add pages here as
# they are converted; rule 2 only applies to these.
CONVERTED = {
    "guide/grove/index.md",
    "guide/grove/inserting.md",
    "guide/grove/querying.md",
    "guide/grove/removing.md",
    "guide/grove/custom_key_types.md",
    "guide/graph/index.md",
    "guide/graph/building.md",
    "guide/graph/navigating.md",
    "guide/graph/editing.md",
}

FENCE = re.compile(r"^(:{3,})\{(tab-set|tab-item)\}\s*(.*)$")
CLOSE = re.compile(r"^(:{3,})\s*$")
HEADING = re.compile(r"^#{1,6}\s")


def check(path: Path, rel: str) -> list[str]:
    errors = []
    stack = []  # (colons, kind, line, titles)
    in_code = False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if m := FENCE.match(line):
            colons, kind, title = m.groups()
            if kind == "tab-item" and stack and stack[-1][1] == "tab-set":
                stack[-1][3].append(title.strip())
            stack.append((len(colons), kind, n, []))
            continue
        if (m := CLOSE.match(line)) and stack and stack[-1][0] == len(m.group(1)):
            colons, kind, start, titles = stack.pop()
            if kind == "tab-set":
                has_cpp = any("cpp_tab" in t for t in titles)
                has_py = any("py_tab" in t for t in titles)
                if not (has_cpp and has_py and len(titles) == 2):
                    errors.append(f"{rel}:{start}: tab-set needs exactly one C++ and one Python tab, got {titles}")
            continue
        if rel in CONVERTED and HEADING.match(line) and any(k == "tab-item" for _, k, _, _ in stack):
            errors.append(f"{rel}:{n}: heading inside a tab — move it above the tab-set")
    for colons, kind, start, _ in stack:
        errors.append(f"{rel}:{start}: unclosed {kind}")
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "source")
    errors = []
    for path in sorted(root.rglob("*.md")):
        errors += check(path, path.relative_to(root).as_posix())
    for e in errors:
        print(e, file=sys.stderr)
    print(f"tab parity: {'FAIL' if errors else 'ok'} ({len(errors)} issue(s))", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())