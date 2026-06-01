#!/usr/bin/env python3
"""Semantic rule checks that Ruff cannot express. Wired into `make check`.

Canonical source: _devtools/rules_check.py (vendored into each bot's scripts/).

Checks:
  money-float : `float` used for a monetary value (price/amount/balance/...).
                Money must be Decimal - IEEE754 rounding causes billing drift
                (0.1 + 0.2 != 0.3). Suppress a false positive with a trailing
                `# money-ok` comment on the same line.

Usage:  python scripts/rules_check.py [PATH ...]   (default: current dir)
Exit 1 if any violation is found, 0 otherwise. Stdlib only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Money-flavored identifier fragments (ru + en).
_MONEY = (
    r"(?:price|amount|balance|cost|total|subtotal|payment|payout|refund|"
    r"sum|fee|tariff|stars|сумм|стоим|баланс|цена|оплат|выплат|доля)"
)
# `money_name: float`  (annotation)
_ANNOT = re.compile(rf"\b\w*{_MONEY}\w*\s*:\s*float\b", re.IGNORECASE)
# `float( ... money_name ... )`  (cast)
_CAST = re.compile(rf"\bfloat\(\s*[^)]*{_MONEY}", re.IGNORECASE)

_SKIP_DIRS = {
    ".venv", ".git", "node_modules", "migrations", "versions",
    "__pycache__", ".cursor", ".mypy_cache", ".ruff_cache",
}


def _iter_py(roots: list[str]):  # noqa: ANN202
    for root in roots:
        for p in Path(root).rglob("*.py"):
            if _SKIP_DIRS & set(p.parts):
                continue
            posix = p.as_posix()
            if "/tests/" in posix or p.name.startswith("test_"):
                continue
            yield p


def main(argv: list[str]) -> int:
    roots = argv[1:] or ["."]
    hits: list[tuple[Path, int, str]] = []
    for p in _iter_py(roots):
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(lines, 1):
            if "# money-ok" in line:
                continue
            if _ANNOT.search(line) or _CAST.search(line):
                hits.append((p, i, line.strip()))
    if hits:
        print("rules_check FAIL: float used for money (use Decimal; suppress with `# money-ok`):")
        for p, i, line in hits:
            print(f"  {p}:{i}: {line}")
        return 1
    print("rules_check ok: no money-float")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
