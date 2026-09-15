"""Generic UI Ref -- host-independent base for the widget kit.

A Ref is a Nu Ref whose storage is a client rendering surface (a browser
tab, in nudle's case). `_wire_type` is the identifier the client uses to
pick a renderer; the methods a Ref exposes (`set`, `append`, `on_change`,
...) decide which interactions it accepts.

Built on `StructuredRef` (parent chain, `_root_shape`). Address
resolution walks the on-tree parent chain and returns the segments as a
tuple, same as `nustd.kv` does. Nothing outside the chain gets a say: a
segment is in the address because something navigated through it, never
because a class named itself. A nudle Page contributes its segment the
same way a Section does, by being reached through the slot that declares
it. Async-only: nustd.ui is a browser fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from typing_extensions import Self

from nu.domains.shape import Slot
from nu.domains.shape.refs.base import StructuredRef
from nu.engine.structure import Declared


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime


__all__ = ["Ref"]


def _wire_type_of(ref_or_section_cls: type) -> str:
    """Browser component a Ref or Section class renders as.

    A plain attribute read, no search. Every Ref and Section the kit ships
    declares its own ``_wire_type``, and a user subclass (``class MyForm(Row)``)
    inherits it the ordinary Python way, so it reports ``Row`` and the browser
    registry resolves it. Out-of-tree Refs that register their own component
    declare the ClassVar too; that is the whole mechanism, there is no
    separate escape hatch. Anything that declares nothing falls back to its
    own class name.
    """
    return getattr(ref_or_section_cls, "_wire_type", "") or ref_or_section_cls.__name__


def _level_type(term: object) -> str:
    """Wire type the browser renders this level with.

    A SectionRef is substrate: what the browser draws is the Section class
    it carries, same as the boot batch reports. Everything else is the
    ref class itself.
    """
    section_cls = getattr(term, "_payload", {}).get("section_cls")
    return _wire_type_of(section_cls if section_cls is not None else type(term))


class Ref(StructuredRef):
    """Base for Refs backed by a client rendering surface. Async-only.

    A Ref with a single semantically primary value exposes `set()` for it
    (`TextRef.set(text)`, `SliderRef.set(n)`); everything else it can drive
    gets its own `set_*`. A container has no primary value, so it has no
    `set()` at all -- see the `nustd.ui.refs` package docstring.
    """

    _requires_async = Declared(value=True, name="requires_async")

    # Browser component this Ref renders as. Every Ref the kit ships declares
    # its own; subclasses inherit it, which is how a user subclass renders as
    # its nearest shipped ancestor. Empty means "fall back to the class name".
    _wire_type: ClassVar[str] = ""

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
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

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
