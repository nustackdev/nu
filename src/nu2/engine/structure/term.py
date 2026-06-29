"""Term: the primitive node of an engine description, and its metaclass.

A Term is layer 0's node: a kind (its class), an ordered tuple of child
Terms, and an opaque payload. It is pure immutable construction data with
no parent and no position; an application is a Term-rooted DAG.

The :class:`TermMeta` metaclass collects :class:`Attribute` declarations off
the class body, populating the per-class :attr:`Term.attributes` mapping.
The compile phase consumes this together with the tree-wide
:class:`~nu2.engine.structure.schema.Schema`.

``Term`` carries two type parameters:

- ``R_contra`` -- the concrete Runtime emitted thunks close over. A
  language layer narrows it (e.g. ``nu2.lang.runtime.Runtime``) so thunks have access to
  whatever per-drive state the language needs. The engine bound is the
  bare :class:`~nu2.engine.evaluation.Runtime` Protocol: only ``eval`` /
  ``aeval`` dispatch are guaranteed. ``R`` appears only in **input**
  positions (the thunk's argument), so it is **contravariant**.
- ``V_co`` -- the value type this Term yields. ``eval`` returns ``V``;
  the sync thunk returned by ``compile`` has signature ``(R) -> V``, and
  the async thunk returned by ``acompile`` has signature
  ``(R) -> Awaitable[V]``. ``V`` appears only in **output** positions, so
  it is **covariant**. Children are heterogeneous and stay opaque
  (``Callable[[R], object]``).

The variance markers require legacy ``TypeVar`` + ``Generic`` rather than
the PEP 695 inline form, since PEP 695 has no explicit variance syntax.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from .attribute import Attribute, Declared


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import ClassVar, Self

    from nu2.engine.evaluation import Runtime

__all__ = ["Term", "TermMeta"]


R_contra = TypeVar("R_contra", bound="Runtime", contravariant=True)
V_co = TypeVar("V_co", covariant=True)


class TermMeta(type):
    """Metaclass that collects :class:`Attribute` declarations off the class body.

    For each class created, walks the MRO and assembles a flat mapping from
    attribute name to :class:`Attribute` instance, stored as the class
    attribute ``attributes``. Class-body declarations that omit ``name``
    inherit it from the binding name.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
    ) -> TermMeta:
        """Build the class and populate its ``attributes`` mapping."""
        cls = super().__new__(mcs, name, bases, namespace)
        attributes: dict[str, Declared] = {}
        for klass in reversed(cls.__mro__):
            for key, value in vars(klass).items():
                if not isinstance(value, Attribute):
                    continue
                if value.name is None:
                    value.name = key
                attributes[value.name] = value  # type: ignore[assignment]
        cls.attributes = attributes  # type: ignore
        return cls


class Term(Generic[R_contra, V_co], metaclass=TermMeta):  # noqa: UP046  # PEP 695 has no variance markers
    """Pure immutable construction data: a kind, children, and a payload.

    A description is a DAG of Terms. Constructing one builds a nested
    immutable value and nothing else -- no store, no evaluation, no checks.
    Attribute values and runtime thunks are produced later by the compile
    phase and live on the resulting Program.

    Subclasses override :meth:`compile` (and :meth:`acompile` for the async
    path) to emit a thunk that consumes precompiled child thunks. The
    fallback default invokes :meth:`eval` / :meth:`aeval`, which raise
    ``NotImplementedError`` on the base Term -- a concrete kind must
    implement at least one of the two paths.

    Type parameters:

    - ``R_contra`` -- the concrete Runtime thunks close over. **Contravariant**
      since ``R`` is consumed only in input positions. A language layer
      narrows it (``class Nu(Term[Runtime, V_co])``); the engine bound is
      the bare :class:`Runtime` Protocol.
    - ``V_co`` -- the value type this Term yields. **Covariant** since
      ``V`` appears only in output positions. The sync thunk returned by
      :meth:`compile` is ``(R) -> V``; the async thunk returned by
      :meth:`acompile` is ``(R) -> Awaitable[V]``.
    """

    attributes: ClassVar[dict[str, Declared]]
    """Per-class mapping ``name -> Declared``, populated by :class:`TermMeta`."""

    def __init__(self, *children: Term) -> None:
        self.children: tuple[Term, ...] = children
        self.payload: dict[str, object] = {}

    # --- construction -------------------------------------------------------

    def with_children(self, *children: Term) -> Self:
        """Return a variant of this Term with different children.

        The original is untouched; the variant shares the same payload.
        """
        variant = object.__new__(type(self))
        variant.children = children
        variant.payload = self.payload
        return variant

    # --- compile hooks ------------------------------------------------------

    def compile(
        self, nid: int, children: tuple[Callable[[R_contra], object], ...]
    ) -> Callable[[R_contra], V_co]:
        """Build a sync thunk ``(rt) -> V`` for this Term at ``nid``.

        ``children`` is the tuple of precompiled child thunks. Atoms on the
        hot path override this to capture ``children`` and call them
        directly, skipping the ``Runtime.eval`` / ``terms[nid].eval`` double
        indirection. The default delegates to :meth:`eval`.
        """

        def thunk(rt: R_contra) -> V_co:
            return self.eval(rt, nid)

        return thunk

    def acompile(
        self, nid: int, children: tuple[Callable[[R_contra], object], ...]
    ) -> Callable[[R_contra], Awaitable[V_co]]:
        """Build an async thunk ``(rt) -> Awaitable[V]`` for this Term at ``nid``.

        ``children`` is the tuple of precompiled async child thunks. Atoms
        on the hot path override this to capture ``children`` and call them
        directly; the default delegates to :meth:`aeval`.
        """

        async def athunk(rt: R_contra) -> V_co:
            return await self.aeval(rt, nid)

        return athunk

    # --- evaluation fallbacks ----------------------------------------------

    def eval(self, rt: R_contra, nid: int) -> V_co:
        """Synchronous evaluation hook for the default :meth:`compile` thunk.

        Concrete Terms either override :meth:`compile` (typical, hot path)
        or override this; the base raises so a missing implementation
        surfaces as a clear error rather than at thunk-call time with a
        cryptic attribute lookup.
        """
        msg = f"{type(self).__name__}.eval is not implemented"
        raise NotImplementedError(msg)

    async def aeval(self, rt: R_contra, nid: int) -> V_co:
        """Asynchronous sibling of :meth:`eval`.

        Concrete Terms either override :meth:`acompile` or override this;
        the base raises.
        """
        msg = f"{type(self).__name__}.aeval is not implemented"
        raise NotImplementedError(msg)

    # --- repr ---------------------------------------------------------------

    def __repr__(self) -> str:
        if "name" in self.payload:
            return str(self.payload["name"])
        if "value" in self.payload:
            return repr(self.payload["value"])
        if not self.children:
            return type(self).__name__
        inner = ", ".join(repr(child) for child in self.children)
        return f"{type(self).__name__}({inner})"
