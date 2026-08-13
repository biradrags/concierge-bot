#!/usr/bin/env python3
"""Semantic rule checks that Ruff cannot express. Wired into `make check` + CI.

Canonical source: _infra/bira-scaffold/template/scripts/rules_check.py (this file);
_devtools/rules_check.py is a generated mirror (`make sync-devtools`).
Edit here, then re-vendor (`cp`) into each bot AND suppress that bot's own hits -
suppression comments are per-repo, so do not blind-copy them.

Each check flags a canon violation Ruff can't see. Suppress one verified false
positive with the check's trailing `# <token>-ok` comment on the offending line.

Checks (id : token : rule):
  money-float      : money-ok          : `float` on a monetary value -> Decimal
                     (IEEE754 billing drift, 0.1 + 0.2 != 0.3).
  layer-import     : layer-import-ok   : core/dto/dao importing tgbot/maxbot ->
                     layer inversion; the clean layers must not depend on UI.
  per-call-session : per-call-session-ok: aiohttp.ClientSession()/httpx.AsyncClient()
                     outside di/ -> build once in Scope.APP, reuse (socket
                     exhaustion + TCP/TLS handshake per call).
  broad-except     : broad-except-ok   : `except BaseException` -> swallows
                     CancelledError/KeyboardInterrupt, breaks async cancellation.
                     Use `except Exception` (+ re-raise CancelledError at boundary).
  html-escape      : html-escape-ok    : f-string builds HTML tags with {interp}
                     and no html.escape on the line -> markup injection of a
                     client/AI string. Low precision: suppress verified FP.
  dao-raise        : dao-raise-ok      : `raise` inside dao/ -> DAO returns None,
                     services raise (layer contract).

Usage:  python scripts/rules_check.py [PATH ...]   (default: current dir)
Exit 1 if any violation is found, 0 otherwise. Stdlib only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# --- money-float -----------------------------------------------------------
_MONEY = (
    r"(?:price|amount|balance|cost|total|subtotal|payment|payout|refund|"
    r"sum|fee|tariff|stars|сумм|стоим|баланс|цена|оплат|выплат|доля)"
)
_MONEY_ANNOT = re.compile(rf"\b\w*{_MONEY}\w*\s*:\s*float\b", re.IGNORECASE)
_MONEY_CAST = re.compile(rf"\bfloat\(\s*[^)]*{_MONEY}", re.IGNORECASE)

# --- other checks ----------------------------------------------------------
_LAYER_IMPORT = re.compile(r"\b(?:from|import)\s+\S*\b(?:tgbot|maxbot)\b")
_SESSION = re.compile(r"\b(?:ClientSession|AsyncClient)\s*\(")
_BROAD_EXCEPT = re.compile(r"\bexcept\s+BaseException\b")
_DAO_RAISE = re.compile(r"^\s*raise\b")
_HTML_FSTR = re.compile(
    r"""f(['"]).*<[a-zA-Z][^>]*>.*\{[^}]+\}.*\1"""
)

_SKIP_DIRS = {
    ".venv", ".git", "node_modules", "migrations", "versions",
    "__pycache__", ".cursor", ".mypy_cache", ".ruff_cache",
}


def _in_layer(path: Path, *names: str) -> bool:
    return bool(set(path.parts) & set(names))


def _money(path: Path, line: str) -> bool:
    return bool(_MONEY_ANNOT.search(line) or _MONEY_CAST.search(line))


def _layer_import(path: Path, line: str) -> bool:
    return _in_layer(path, "core", "dto", "dao") and bool(_LAYER_IMPORT.search(line))


def _per_call_session(path: Path, line: str) -> bool:
    # di/ owns shared Scope.APP clients; allow dir `di` and module `di.py`.
    if "di" in path.parts or path.stem == "di":
        return False
    return bool(_SESSION.search(line))


def _broad_except(path: Path, line: str) -> bool:
    return bool(_BROAD_EXCEPT.search(line))


def _dao_raise(path: Path, line: str) -> bool:
    return _in_layer(path, "dao") and bool(_DAO_RAISE.search(line))


def _html_escape(path: Path, line: str) -> bool:
    if "html.escape" in line:
        return False
    return bool(_HTML_FSTR.search(line))


# (id, suppress-token, predicate)
_CHECKS = (
    ("money-float", "money-ok", _money),
    ("layer-import", "layer-import-ok", _layer_import),
    ("per-call-session", "per-call-session-ok", _per_call_session),
    ("broad-except", "broad-except-ok", _broad_except),
    ("html-escape", "html-escape-ok", _html_escape),
    ("dao-raise", "dao-raise-ok", _dao_raise),
)


def _iter_py(roots: list[str]):
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
    hits: list[tuple[str, Path, int, str]] = []
    for p in _iter_py(roots):
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(lines, 1):
            for check_id, token, predicate in _CHECKS:
                if f"# {token}" in line:
                    continue
                if predicate(p, line):
                    hits.append((check_id, p, i, line.strip()))
    if hits:
        print("rules_check FAIL (suppress a verified false positive with `# <token>-ok`):")
        for check_id, p, i, line in sorted(hits, key=lambda h: (h[0], str(h[1]), h[2])):
            print(f"  [{check_id}] {p}:{i}: {line}")
        return 1
    print("rules_check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
