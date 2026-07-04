"""inline_refs — virtuals substrate ref inlining deformation.

Walks the term tree bottom-up. Two cases are inlined into a FlatRef:

* A bare virtuals Ref appearing as a tree child (v2 layout: ops carry their
  refs as regular children). Replacing the ref itself with a FlatRef is the
  usual path -- ``map_nodes`` rebuilds the enclosing op via ``with_children``
  so the FlatRef lands in the same slot.

* An op node exposing its ref via a ``.ref`` attribute (legacy layout kept
  by ``nu.nudle`` and a few compat ops). Rebuild via
  ``reconstruct_with_flat_ref`` so the ``.ref`` attribute stays in sync.

Either way, the deformation walks the Ref's parent chain to collect
static/dynamic address segments and type markers, and emits a FlatRef with
a pre-resolved path tuple of ``(address, type_marker)`` segments.
"""

from __future__ import annotations

from nu.domains.shape.refs.base import _StructuredRef
from nu.domains.shape.rewrite import reconstruct_with_flat_ref, walk_ref_chain
from nu.tree import map_nodes
from nu.virtuals.refs.base import PrimitiveRef, ViewRef
from nu.virtuals.refs.flat import FlatRef


__all__ = [
    "inline_refs",
]


def inline_refs[N](tree: N) -> N:
    """Replace virtuals Ref parent-chains with flat FlatRefs."""
    return map_nodes(tree, _try_inline_ref, order="bottom_up")


def _try_inline_ref(node: object) -> object:
    """If node is (or holds) a virtuals Ref, replace it with a FlatRef."""
    if isinstance(node, (ViewRef, PrimitiveRef)):
        return _flatten(node)

    ref = getattr(node, "ref", None)
    if ref is None or not isinstance(ref, _StructuredRef):
        return node
    if not isinstance(ref, (ViewRef, PrimitiveRef)):
        return node
    return reconstruct_with_flat_ref(node, _flatten(ref))


def _flatten(ref: ViewRef | PrimitiveRef) -> FlatRef:
    """Build a FlatRef from a virtuals Ref, walking its parent chain."""
    is_primitive = isinstance(ref, PrimitiveRef)

    addresses, address_terms = walk_ref_chain(ref)

    # Collect type markers from each ref in the chain (root-to-leaf).
    type_markers: list[type | None] = []
    current: object = ref
    while current is not None:
        type_markers.append(getattr(current, "_type_marker", None))
        current = current.parent_ref  # type: ignore[attr-defined]
    type_markers.reverse()

    dynamic: list[tuple[int, object]] = [
        (i, term) for i, term in enumerate(address_terms) if term is not None
    ]

    static_path = tuple(zip(addresses, type_markers, strict=True))
    return FlatRef(
        static_path=static_path,
        root_shape=ref.get_root_shape(),
        is_primitive=is_primitive,
        dynamic_segments=tuple(dynamic) if dynamic else None,
    )
