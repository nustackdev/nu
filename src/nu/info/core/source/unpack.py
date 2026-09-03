"""Read how many names a function unpacks a variable into. No Nu knowledge.

Some structural facts are stated in code rather than in a signature. A
function that opens with ``left, right = children`` says two out loud, and
that is worth reading when the signature says only "any number".

Source-reading, so it is a checker, not a hot path.
"""

from __future__ import annotations

import ast
import textwrap

from nu.info.core.source.code import read_source


__all__ = ["unpacked_count"]


def unpacked_count(func: object, variable: str) -> int | None:
    """How many names ``func`` unpacks ``variable`` into.

    Args:
        func: the function to read.
        variable: the name being unpacked, e.g. ``"children"``.

    Returns:
        The widest unpack found, so a function with both a one-name and a
        two-name branch reads as two. None when the source cannot be read or
        when the variable is never unpacked at all.
    """
    source = read_source(func)
    if source is None:
        return None
    try:
        tree = ast.parse(textwrap.dedent(source.text))
    except SyntaxError:
        return None
    counts = {
        len(node.targets[0].elts)
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Tuple | ast.List)
        and isinstance(node.value, ast.Name)
        and node.value.id == variable
    }
    return max(counts) if counts else None
