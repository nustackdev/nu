"""nu-mem — Nu Shapes fabric adapter for in-memory state.

Plain nested Python dicts as the data bag. No storage backend, no views,
no reactivity. Just dicts.

Usage::

    import nu_mem as nm
    from nu import Context
    from nu.domains.shape import Shape

    class User(Shape):
        name = nm.StrRef.slot()
        age = nm.IntRef.slot()

    data = {}
    ctx = Context().bind(dict, data, User)
"""

from nu_mem.refs import (
    BoolRef,
    BytesRef,
    DictRef,
    FloatRef,
    IntRef,
    ItemRef,
    ListRef,
    RefBase,
    SetRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
)


# --- ported incrementally during the P2 v2 port ------------------------------
# Collection refs (DictRef/ListRef/SetRef/ShapeRef/ShapesDictRef/ShapesListRef),
# the stdlib-typed refs (-> P4), jqueue (deferred pass), and tree/inline_refs are
# re-added here as each lands on the v2 substrate seam.


__all__ = [
    "BoolRef",
    "BytesRef",
    "DictRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ListRef",
    "RefBase",
    "SetRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "StrRef",
]
