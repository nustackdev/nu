"""``Form``: the node every value form extends.

A form is the surface sub-shape of Span (sort ``FORM``, declared by the
``_Form`` kind in ``nu.lang.kinds``). It wraps exactly one body, does no work
of its own and forwards the body's yield unchanged, in the body's
cardinality.

This module is the implementation on top of that kind: the one-body check,
the ``type_info`` a typed collection carries, the refusal of a class that is
both a Ref and a Form, and the passthrough compile. The methods a form offers
live on a ``Surface`` (``nu.lang.surface``), mixed in ahead of it::

    class Str(StrSurface, Form[str]): ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from .kinds import Ref, _Form


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from nu.lang.runtime import Runtime
    from nu.lang.typeinfo import TypeInfo


V_co = TypeVar("V_co", covariant=True)

__all__ = ["Form"]


class Form(_Form[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Span that gives its body a typed surface.

    The third Span sub-shape, next to Bracket (lifecycle) and Policy
    (execution). A Form wraps exactly one body, does no work of its own and
    forwards the body's yield unchanged, NULL included. Its cardinality is
    the body's, like every Span, so a Form over a stream is a stream and a
    Form over a scalar is a scalar; the composition matrix lets only a
    yielding body in (a Ref, a Query, an Action, or a Span over one).

    The kind is the node only. The methods (``.upper()``, ``+``, ``.pop()``)
    come from a ``Surface`` mixed in ahead of it, which a Ref shares without
    becoming a Form: ``Str(StrSurface, Form)`` is the value node and
    ``StrRef(MutableItemRef, StrSurface)`` the Ref.

    Compiles to a passthrough over the body's thunk. The node is kept rather
    than elided, so its nid, its attributes and its place in an inspected
    tree stay where the user wrote it.
    """

    def __init__(self, *children: object, type_info: TypeInfo | None = None) -> None:
        if len(children) != 1:
            msg = f"{type(self).__name__} wraps exactly one body, got {len(children)}"
            raise TypeError(msg)
        super().__init__(*children)
        self._type_info: TypeInfo | None = type_info
        """The declared types the body's value carries (a typed collection's
        key and element), so the surface's own ops stay typed. None when
        nothing is declared."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if issubclass(cls, Ref):
            # A Ref shares a form's methods through its Surface, never the
            # node: it would inherit a sort and a compile it must then shadow.
            msg = (
                f"{cls.__name__} is both a Ref and a Form: mix the family's "
                "Surface into the Ref instead of its Form"
            )
            raise TypeError(msg)

    @property
    def _source(self) -> Any:  # noqa: ANN401
        """The wrapped body Term."""
        return self._children[0]

    def _compile(self, nid: int, children: tuple[Callable[..., Any], ...]) -> Callable[..., Any]:
        (body,) = children

        def thunk(rt: Runtime) -> object:
            return body(rt)

        return thunk

    def _acompile(
        self, nid: int, children: tuple[Callable[..., Any], ...]
    ) -> Callable[..., Awaitable[Any]]:
        (body,) = children

        async def athunk(rt: Runtime) -> object:
            return await body(rt)

        return athunk
