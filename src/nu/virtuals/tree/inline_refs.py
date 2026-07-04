"""inline_refs — retired. Runtime path resolution superseded ref flattening.

With the parent on the tree (``children[0]``) and the ``(addr, marker)`` path
resolved at runtime by walking that chain, a virtuals ``StructuredRef`` already
resolves dynamic parent keys with no flattening pass, and the op interactions
run against it through the same ``_resolve_path(rt, nid)`` / ``_fetch_parent_view``
interface FlatRef used to provide.

FlatRef was an O(1)-static-path optimization. It no longer composes with the
on-tree parent (a bottom-up ``map_nodes`` would flatten a parent before its
leaf, truncating the chain walk) and is no longer needed for correctness. This
pass is now identity. Kept as a no-op so existing call sites still import and
run; drop the calls at leisure.
"""

from __future__ import annotations


__all__ = ["inline_refs"]


def inline_refs[N](tree: N) -> N:
    """Identity: ref flattening is retired (runtime resolution handles chains)."""
    return tree
