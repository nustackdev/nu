"""inline_refs — dict substrate ref inlining deformation.

Walks the term tree bottom-up. For each morphism node that holds a dict
substrate Ref (RefBase), walks the Ref's parent chain at deformation time,
collects static/dynamic address segments, and creates an FlatRef with
a pre-resolved path tuple.
"""

from __future__ import annotations

from everybase.meta.transform import map_nodes
from everydict.meta.flat_ref import FlatRef
from everydict.refs.base import RefBase
from everyshape.meta.deform import reconstruct_with_flat_ref, walk_ref_chain
from everyshape.refs.base import Ref


__all__ = [
    "inline_refs",
]


def inline_refs[N](tree: N) -> N:
    """Replace dict Ref parent-chains with flat FlatRefs.

    Args:
        tree: Term tree root.

    Returns:
        New tree with dict Ref chains replaced by FlatRefs.
    """
    return map_nodes(tree, _try_inline_ref, order="bottom_up")


def _try_inline_ref(node: object) -> object:
    """If node holds a dict Ref, replace it with FlatRef."""
    ref = getattr(node, "ref", None)
    if ref is None or not isinstance(ref, Ref):
        return node

    # Only handle dict substrate refs
    if not isinstance(ref, RefBase):
        return node

    # Walk parent chain at deformation time
    addresses, address_terms = walk_ref_chain(ref)

    # Build dynamic segments list
    dynamic: list[tuple[int, object]] = []
    for i, term in enumerate(address_terms):
        if term is not None:
            dynamic.append((i, term))

    root_shape = ref.get_root_shape()
    static_path = tuple(addresses)
    dyn = tuple(dynamic) if dynamic else None

    inline = FlatRef(
        static_path=static_path,
        root_shape=root_shape,
        dynamic_segments=dyn,
    )

    return reconstruct_with_flat_ref(node, inline)
