"""Term: the primitive node of an engine description, and its metaclass.

A Term is layer 0's node: a kind (its class), its fields (plain instance
attributes set once in ``__init__``), and an ordered tuple of child Terms.
It is pure immutable construction data with no parent and no position; an
application is a Term-rooted DAG.

The :class:`TermMeta` metaclass collects :class:`Attribute` declarations off
the class body, populating the per-class :attr:`Term._attributes` mapping.
The compile phase consumes this together with the tree-wide
:class:`~nu.engine.structure.schema.Schema`.

``Term`` carries two type parameters:

- ``R_contra`` -- the concrete Runtime emitted thunks close over. A
  language layer narrows it (e.g. ``nu.lang.runtime.Runtime``) so thunks have access to
  whatever per-drive state the language needs. The engine bound is the
  bare :class:`~nu.engine.evaluation.Runtime` Protocol: only ``eval`` /
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

import copy
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from .attribute import Attribute, Declared


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable
    from typing import ClassVar

    from typing_extensions import Self

    from nu.engine.evaluation import Runtime

__all__ = ["FrozenTermError", "Term", "TermMeta"]


R_contra = TypeVar("R_contra", bound="Runtime", contravariant=True)
V_co = TypeVar("V_co", covariant=True)

_FROZEN = "_frozen"
"""Instance ``__dict__`` key :class:`TermMeta` sets once construction returns."""


class FrozenTermError(AttributeError):
    """Raised on writing or deleting an attribute of a constructed Term.

    Fields are set in ``__init__`` and never after; a variant is built with
    :meth:`Term.evolve`. Subclasses ``AttributeError`` (as dataclasses'
    ``FrozenInstanceError`` does) so code that probes with ``setattr`` under
    ``except AttributeError`` (typing setting ``__orig_class__`` on a generic
    instance) keeps working.
    """


class TermMeta(type):
    """Metaclass that collects :class:`Attribute` declarations off the class body.

    For each class created, walks the MRO and assembles a flat mapping from
    attribute name to :class:`Attribute` instance, stored as the class
    attribute ``_attributes``. Class-body declarations that omit ``name``
    inherit it from the binding name.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
    ) -> TermMeta:
        """Build the class and populate its ``_attributes`` mapping."""
        cls = super().__new__(mcs, name, bases, namespace)
        attributes: dict[str, Declared] = {}
        for klass in reversed(cls.__mro__):
            for key, value in vars(klass).items():
                if not isinstance(value, Attribute):
                    continue
                if value.name is None:
                    value.name = key
                attributes[value.name] = value  # type: ignore[assignment]
        cls._attributes = attributes  # type: ignore
        return cls

    def __call__(cls, *args: object, **kwargs: object) -> Any:  # noqa: ANN401 -- Any keeps __init__'s signature for type checkers
        """Construct as usual, then freeze the instance.

        Fires once, after the outermost ``__init__`` returns, so a subclass
        ``__init__`` calling ``super().__init__`` (or reassigning a field the
        base set) still writes freely. The flag lives in the instance
        ``__dict__``, so copies and unpickled Terms arrive frozen.
        """
        instance = super().__call__(*args, **kwargs)
        if isinstance(instance, Term):
            instance.__dict__[_FROZEN] = True
        return instance


class Term(Generic[R_contra, V_co], metaclass=TermMeta):  # PEP 695 has no variance markers
    """Pure immutable construction data: a kind, fields, and children.

    A description is a DAG of Terms. Constructing one builds a nested
    immutable value and nothing else -- no store, no evaluation, no checks.
    Attribute values and runtime thunks are produced later by the compile
    phase and live on the resulting Program.

    Subclasses override :meth:`_compile` (and :meth:`_acompile` for the async
    path) to emit a thunk that consumes precompiled child thunks. The
    fallback default invokes :meth:`_eval` / :meth:`_aeval`, which raise
    ``NotImplementedError`` on the base Term -- a concrete kind must
    implement at least one of the two paths.

    Type parameters:

    - ``R_contra`` -- the concrete Runtime thunks close over. **Contravariant**
      since ``R`` is consumed only in input positions. A language layer
      narrows it (``class Nu(Term[Runtime, V_co])``); the engine bound is
      the bare :class:`Runtime` Protocol.
    - ``V_co`` -- the value type this Term yields. **Covariant** since
      ``V`` appears only in output positions. The sync thunk returned by
      :meth:`_compile` is ``(R) -> V``; the async thunk returned by
      :meth:`_acompile` is ``(R) -> Awaitable[V]``.
    """

    _attributes: ClassVar[dict[str, Declared]]
    """Per-class mapping ``name -> Declared``, populated by :class:`TermMeta`."""

    def __init__(self, *children: Term) -> None:
        self._children: tuple[Term, ...] = children

    # --- construction -------------------------------------------------------

    def __setattr__(self, name: str, value: object) -> None:
        if _FROZEN in self.__dict__:
            msg = f"cannot set {name!r} on a constructed {type(self).__name__}; use evolve()"
            raise FrozenTermError(msg)
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if _FROZEN in self.__dict__:
            msg = f"cannot delete {name!r} on a constructed {type(self).__name__}; use evolve()"
            raise FrozenTermError(msg)
        object.__delattr__(self, name)

    def evolve(self, children: Iterable[Term] | None = None, **fields: object) -> Self:
        """Return a variant of this Term: same kind, some children or fields replaced.

        A shallow copy of this Term with ``children`` (when given) as its new
        child tuple and each keyword overriding the field of that name. The
        original is untouched. Fields not overridden are shared by reference
        with the original, which is safe since fields are never written after
        ``__init__``. The variant is frozen like the original: the copy
        carries the flag, and the overrides go past the guard here only.
        """
        variant = copy.copy(self)
        if children is not None:
            object.__setattr__(variant, "_children", tuple(children))
        for name, value in fields.items():
            object.__setattr__(variant, name, value)
        return variant

    # --- compile hooks ------------------------------------------------------

    def _compile(
        self, nid: int, children: tuple[Callable[[R_contra], object], ...]
    ) -> Callable[[R_contra], V_co]:
        """Build a sync thunk ``(rt) -> V`` for this Term at ``nid``.

        ``children`` is the tuple of precompiled child thunks. Atoms on the
        hot path override this to capture ``children`` and call them
        directly, skipping the ``Runtime.eval`` / ``terms[nid]._eval`` double
        indirection. The default delegates to :meth:`_eval`.
        """

        def thunk(rt: R_contra) -> V_co:
            return self._eval(rt, nid)

        return thunk

    def _acompile(
        self, nid: int, children: tuple[Callable[[R_contra], object], ...]
    ) -> Callable[[R_contra], Awaitable[V_co]]:
        """Build an async thunk ``(rt) -> Awaitable[V]`` for this Term at ``nid``.

        ``children`` is the tuple of precompiled async child thunks. Atoms
        on the hot path override this to capture ``children`` and call them
        directly; the default delegates to :meth:`_aeval`.
        """

        async def athunk(rt: R_contra) -> V_co:
            return await self._aeval(rt, nid)

        return athunk

    # --- evaluation fallbacks ----------------------------------------------

    def _eval(self, rt: R_contra, nid: int) -> V_co:
        """Synchronous evaluation hook for the default :meth:`_compile` thunk.

        Concrete Terms either override :meth:`_compile` (typical, hot path)
        or override this; the base raises so a missing implementation
        surfaces as a clear error rather than at thunk-call time with a
        cryptic attribute lookup.
        """
        msg = f"{type(self).__name__}._eval is not implemented"
        raise NotImplementedError(msg)

    async def _aeval(self, rt: R_contra, nid: int) -> V_co:
        """Asynchronous sibling of :meth:`_eval`.

        Concrete Terms either override :meth:`_acompile` or override this;
        the base raises.
        """
        msg = f"{type(self).__name__}._aeval is not implemented"
        raise NotImplementedError(msg)

    # --- pickle -------------------------------------------------------------

    def __getstate__(self) -> dict:
        """Return instance state for pickle.

        Subclasses that override ``__getattr__`` (e.g. ``ShapeRef``,
        ``SectionRef``) would infinite-loop vanilla pickle since pickle
        probes for ``__getstate__`` / ``__setstate__`` via ``__getattr__``.
        Defining these on the base short-circuits that lookup.
        """
        return self.__dict__.copy()

    def __setstate__(self, state: dict) -> None:
        """Restore instance state from pickle without triggering ``__getattr__``."""
        self.__dict__.update(state)

    # --- repr ---------------------------------------------------------------

    def __repr__(self) -> str:
        if not self._children:
            return type(self).__name__
        inner = ", ".join(repr(child) for child in self._children)
        return f"{type(self).__name__}({inner})"
