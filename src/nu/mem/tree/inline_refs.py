"""inline_refs — dict substrate ref inlining deformation.

Walks the term tree bottom-up. Two cases are inlined into a FlatRef:

* A bare mem Ref appearing as a tree child (v2 layout: ops carry their
  refs as regular children). Replacing the ref itself with a FlatRef is
  the usual path -- ``map_nodes`` rebuilds the enclosing op via
  ``with_children`` so the FlatRef lands in the same slot.

* An op node exposing its ref via a ``.ref`` attribute (legacy layout).
  Rebuild via ``reconstruct_with_flat_ref`` so the ``.ref`` attribute
  stays in sync.

Either way, the deformation walks the Ref's parent chain to collect
static / dynamic address segments and emits a FlatRef with a pre-resolved
path tuple.
"""

from __future__ import annotations

from nu.domains.shape.refs.base import _StructuredRef
from nu.domains.shape.rewrite import reconstruct_with_flat_ref, walk_ref_chain
from nu.mem.refs.base import RefBase
from nu.mem.refs.flat import FlatRef
from nu.mem.refs.jqueue import JQueueRef
from nu.tree import map_nodes


__all__ = [
    "inline_refs",
]


# JQueueRef overrides ``compile``/``acompile`` to vivify a janus.Queue at
# its slot on first fetch. FlatRef would replace that with a plain dict
# lookup and lose the vivification, so leave JQueueRef alone.
_NON_FLATTENABLE: tuple[type, ...] = (JQueueRef,)


def _flattenable(ref: object) -> bool:
    return isinstance(ref, RefBase) and not isinstance(ref, _NON_FLATTENABLE)


def inline_refs[N](tree: N) -> N:
    """Replace dict Ref parent-chains with flat FlatRefs."""
    return map_nodes(tree, _try_inline_ref, order="bottom_up")


def _try_inline_ref(node: object) -> object:
    """If node is (or holds) a dict Ref, replace it with a FlatRef."""
    if _flattenable(node):
        return _flatten(node)  # type: ignore[arg-type]

    ref = getattr(node, "ref", None)
    if ref is None or not isinstance(ref, _StructuredRef):
        return node
    if not _flattenable(ref):
        return node
    return reconstruct_with_flat_ref(node, _flatten(ref))


def _flatten(ref: RefBase) -> FlatRef:
    """Build a FlatRef from a mem Ref, walking its parent chain."""
    addresses, address_terms = walk_ref_chain(ref)

    dynamic: list[tuple[int, object]] = [
        (i, term) for i, term in enumerate(address_terms) if term is not None
    ]

    static_path = tuple(addresses)
    return FlatRef(
        static_path=static_path,
        root_shape=ref.get_root_shape(),
        dynamic_segments=tuple(dynamic) if dynamic else None,
    )
