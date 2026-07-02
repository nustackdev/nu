"""Service dispatch: build interaction atoms that call a bound service's methods.

A service is a typed Context binding (``ctx.bind(SolanaClient, client)``) named
by a ``ServiceRef``. Calling one of its methods from inside the tree is the same
move the ``InteractionFactory`` already makes - resolve the child slots, call a
callable, handle sentinels / async / attributes - with one twist: the callable
is not fixed, it is ``getattr(service, method_name)`` where the service is
resolved from slot 0 at run time. So this builds *on* the factory rather than
reinventing it.

``MethodFactory`` is the builder, symmetric to ``InteractionFactory``: pass a
base kind, a class name, and the host method name, and get back a real atom
class whose slot 0 is the service Ref and whose remaining slots are the call
arguments. The base is passed explicitly and is never defaulted, because it *is*
the effect semantics: a read (``ScalarQuery``, slot 0 READ) versus an effectful
call (``ScalarAction`` / ``Command``, slot 0 WRITE). Two attributes default for
the service case and stay overridable: ``deterministic=False`` (an external call
never folds) and, for a Command / Action base, ``mutates={0}`` (the WRITE that
serializes calls on the service's fabric)::

    GetSlot = MethodFactory(ScalarQuery, "GetSlot", "getSlot")
    IntForm(GetSlot(Solana()))            # typed, in-tree read

The ``method_*`` descriptors are the class-body sugar over it, one per base so
the kind is always named at the declaration site (mirroring ``ScalarQueryFactory``
next to ``InteractionFactory``):

- ``method_query(form, name)`` - a pure external read (yields, no mutation).
- ``method_action(form, name)`` - an effectful call that yields.
- ``method_command(name)`` - an effectful call that yields nothing (no Form, the
  same way ``io.print`` returns its Command raw).

On a ``ServiceRef`` subclass each builds its atom once and, on access, returns a
callable that instantiates it with the service Ref in slot 0, resolved from the
Context at run time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Action, Command, InteractionFactory, ScalarAction, ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.forms import Form
    from nu.lang import Nu

    from .refs import ServiceRef


__all__ = [
    "MethodFactory",
    "method_action",
    "method_command",
    "method_query",
]


def MethodFactory[B: Nu](  # noqa: N802 - a class factory; reads as a class at the call site
    base: type[B],
    name: str,
    method_name: str,
    *,
    propagate_sentinels: bool = True,
    **attributes: object,
) -> type[B]:
    """Build an atom class that calls ``method_name`` on the service in slot 0.

    A thin service-flavored ``InteractionFactory``: the built callable is
    ``getattr(service, method_name)(*args, **kwargs)``, with the service
    resolved from slot 0 and the call arguments from slots 1... ``base`` is the
    caller's and carries the effect semantics (``ScalarQuery`` read,
    ``ScalarAction`` / ``Command`` write). ``deterministic`` defaults False and -
    for a Command or Action base - ``mutates`` defaults to slot 0, both
    overridable through ``attributes``.
    """

    def dispatch(service: object, *args: object, **kwargs: object) -> object:
        return getattr(service, method_name)(*args, **kwargs)

    if issubclass(base, (Command, Action)):
        attributes.setdefault("mutates", frozenset({0}))
    attributes.setdefault("deterministic", False)
    return InteractionFactory(
        base, name, dispatch, propagate_sentinels=propagate_sentinels, **attributes
    )


class _ServiceMethod:
    """Shared descriptor behind the ``method_*`` variants.

    Builds its atom class once (via ``MethodFactory``) when the owning service
    class names it, then on access returns a callable that instantiates the atom
    with the service Ref in slot 0. Class access (``Service.slot()``) resolves
    the service from the Context; instance access (``ref.slot()``) targets that
    Ref. A yielding variant wraps the result in ``form``; a command variant
    (``form is None``) returns the raw Command.
    """

    def __init__(
        self,
        base: type[Nu],
        form: type[Form] | None,
        name: str | None,
        **attributes: object,
    ) -> None:
        self._base = base
        self._form = form
        self._explicit = name
        self._attributes = attributes
        self._name = name or ""
        self._atom: type[Nu] | None = None

    def __set_name__(self, owner: type, attr: str) -> None:
        self._name = self._explicit or attr
        self._atom = MethodFactory(
            self._base, f"{owner.__name__}_{self._name}", self._name, **self._attributes
        )

    def __get__(self, obj: ServiceRef | None, objtype: type[ServiceRef] | None = None) -> Callable:
        ref = obj if obj is not None else objtype()
        atom, form = self._atom, self._form

        def call(*args: object, **kwargs: object) -> Nu:
            node = atom(ref, *args, **kwargs)
            return form(node) if form is not None else node

        return call


def method_query(form: type[Form], name: str | None = None, **attributes: object) -> _ServiceMethod:
    """Declare a pure external read on a service class.

    Builds a ``ScalarQuery`` (slot 0 READ) that yields the method's return value
    wrapped in ``form`` - reading external state without mutating the service
    fabric; non-determinism is carried by ``deterministic=False``, not by faking
    a write. Usage: ``slot = method_query(IntForm, "getSlot")``.
    """
    return _ServiceMethod(ScalarQuery, form, name, **attributes)


def method_action(
    form: type[Form], name: str | None = None, **attributes: object
) -> _ServiceMethod:
    """Declare an effectful call that yields a value.

    Builds a ``ScalarAction`` (slot 0 WRITE) that mutates the service fabric and
    yields the method's return value wrapped in ``form``; calls to one service
    serialize. Usage: ``send = method_action(StrForm, "sendTransaction")``.
    """
    return _ServiceMethod(ScalarAction, form, name, **attributes)


def method_command(name: str | None = None, **attributes: object) -> _ServiceMethod:
    """Declare an effectful call that yields nothing.

    Builds a ``Command`` (slot 0 WRITE) run for its effect. It has no value to
    type, so it takes no Form and returns the raw Command - like ``io.print``.
    Usage: ``ping = method_command("ping")``.
    """
    return _ServiceMethod(Command, None, name, **attributes)
