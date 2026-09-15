#!/usr/bin/env python3
"""Fail if the kernel (``packages/nucore``) imports a batteries fabric (``nustd``).

``nucore`` must install and run on its own. Anything under
``packages/nucore/src/`` that does ``import nustd.kv`` / ``from nustd... import ...``
at module scope breaks that, so this hook rejects it.

Only real ``import`` statements are checked -- docstrings and comments are
untouched (they are the documented surface and reference ``nustd.kv`` etc. all
over). A ``try:``-guarded or function-local import is allowed on purpose: that
is the sanctioned escape hatch for a kernel module that wants a fabric when one
happens to be installed.

Usage:  python scripts/check_kernel_boundary.py [files...]
With no arguments, walks the whole kernel tree.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


KERNEL = Path(__file__).resolve().parent.parent / "packages" / "nucore" / "src"


def _batteries(module: str) -> bool:
    """Whether a dotted module name reaches into the batteries package."""
    return module == "nustd" or module.startswith("nustd.")


def _violations(path: Path) -> list[str]:
    """Every module-scope batteries import in one kernel file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: list[str] = []
    # Module scope only: a nested import (inside a def, or under try/except)
    # is the deliberate lazy escape hatch.
    for node in tree.body:
        names: list[tuple[int, str]] = []
        if isinstance(node, ast.Import):
            names = [(node.lineno, a.name) for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [(node.lineno, node.module)]
        for lineno, module in names:
            if _batteries(module):
                out.append(f"{path}:{lineno}: kernel imports batteries module {module}")
    return out


def main(argv: list[str]) -> int:
    """Check the given files (or the whole kernel) and report violations."""
    if argv:
        files = [Path(a).resolve() for a in argv]
        files = [f for f in files if f.suffix == ".py" and KERNEL in f.parents]
    else:
        files = sorted(KERNEL.rglob("*.py"))

    found = [v for f in files for v in _violations(f)]
    for line in found:
        print(line, file=sys.stderr)  # noqa: T201
    if found:
        print(  # noqa: T201
            "\nThe nucore kernel must not depend on nustd. "
            "Move the code, invert the dependency, or import lazily inside the function.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
