"""Generic UI Ref -- host-independent base for the widget kit.

A Ref is a Nu Ref whose storage is a client rendering surface (a browser
tab, in nudle's case). The class name is the wire identifier the client
uses to pick a renderer; the methods a Ref exposes (`store`, `append`,
`changed`, ...) decide which interactions it accepts.

Built on `StructuredRef` (parent chain, `_root_shape`). Address
resolution walks the on-tree parent chain and returns the segments as a
tuple, same as `nu.kv` does. Nothing outside the chain gets a say: a
segment is in the address because something navigated through it, never
because a class named itself. A nudle Page contributes its segment the
same way a Section does, by being reached through the slot that declares
it. Async-only: nu.ui is a browser fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from nu.domains.shape import Slot
from nu.domains.shape.refs.base import StructuredRef
from nu.engine.structure import Declared


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime


__all__ = ["Ref"]


_REFS_PKG = "nu.ui.refs."
_REFS_BASE = f"{_REFS_PKG}base"


def _wire_type(ref_or_section_cls: type) -> str:
    """Canonical (registered) class name for a Ref or Section.

    Out-of-tree Refs (e.g. those shipped by nuspace) may set a
    ``_wire_type_override`` class attribute to name the browser-side
    factory directly, bypassing the MRO walk below. That is the
    escape hatch for packages that register their own factory but
    have no ancestor under ``nu.ui.refs``.

    Otherwise walks the MRO to find the closest ancestor defined inside the
    ``nu.ui.refs`` package (excluding the abstract ``base`` module). User
    subclasses defined outside the package inherit the wire type of their
    nearest packaged ancestor so the browser registry resolves them.
    """
    for base in ref_or_section_cls.__mro__:
        override = base.__dict__.get("_wire_type_override")
        if isinstance(override, str):
            return override
        mod = getattr(base, "__module__", "")
        if not mod.startswith(_REFS_PKG):
            continue
        if mod == _REFS_BASE:
            continue
        return base.__name__
    return ref_or_section_cls.__name__


def _level_type(term: object) -> str:
    """Wire type the browser renders this level with.

    A SectionRef is substrate: what the browser draws is the Section class
    it carries, same as the boot batch reports. Everything else is the
    ref class itself.
    """
    section_cls = getattr(term, "_payload", {}).get("section_cls")
    return _wire_type(section_cls if section_cls is not None else type(term))


class Ref(StructuredRef):
    """Base for Refs backed by a client rendering surface. Async-only."""

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(
        self,
        address: object,
        *,
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        # State lives in ``payload`` (part of the Term identity) so the base
        # ``Term._with_children`` carries it across a tree rewrite -- no override.
        self._payload["segment"] = address

    # --- wire-path resolution ------------------------------------------------

    async def _aresolve_address(self, rt: Runtime, nid: int) -> tuple[str, ...]:
        """Wire path for this Ref: the chain's segments, root-first.

        Walks the on-tree parent chain (``rt.program.children``: ``[0]`` =
        structural parent, ``[1]`` = address) and evaluates each level's
        address child, so a computed segment resolves here like any other
        child. Self plus parents is the whole address; nothing else feeds it.
        """
        segments: list[str] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            segments.append(str(await rt.aeval(kids[1])))
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break  # parent is the ANCHOR -> chain root
            cur = parent
        segments.reverse()
        return tuple(segments)

    async def _aresolve_chain(self, rt: Runtime, nid: int) -> tuple[tuple[str, str, dict], ...]:
        """Same walk as ``_aresolve_address``, annotated per level.

        Returns ``(segment, type, props)`` root-first, one entry per level.
        The term at each level *is* the ref, so its wire type and the props
        its slot declared come straight off it -- no second traversal. The
        browser needs all three to create a component on first write instead
        of being told about it up front.
        """
        levels: list[tuple[str, str, dict]] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            term = rt.program.terms[cur]
            segment = str(await rt.aeval(kids[1]))
            props = dict(getattr(term, "_payload", {}).get("props") or {})
            levels.append((segment, _level_type(term), props))
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break  # parent is the ANCHOR -> chain root
            cur = parent
        levels.reverse()
        return tuple(levels)

    # --- execution (async-only) ----------------------------------------------

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> Any:
            raise RuntimeError("nu.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            raise NotImplementedError(
                f"{type(self).__name__} is display-only; reading is not supported",
            )

        return athunk

    async def _aread(self, rt: Runtime, nid: int) -> Any:
        """Round-trip read of the live client value (input Refs override _acompile)."""
        from .session import Session

        session = rt.ctx.get(Session)
        path = await self._aresolve_address(rt, nid)
        return self._lift(await session.aread(path))

    # --- declaration ---------------------------------------------------------

    @classmethod
    def slot(cls, **props: object) -> Self:
        return Slot(cls, props=props)  # type: ignore[return-value]
