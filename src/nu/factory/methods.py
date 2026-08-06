"""``MethodFactory``: build atoms that call a named method on the slot-0 receiver.

Sibling of ``InteractionFactory`` for the "call this named method on the
receiver" pattern. Works for any object with the named method - a bound
fabric (the ``FabricRef`` case), a proxy, a plain host value. Slot 0 is the
receiver; slots 1... are the call arguments.

``MethodFactory`` sets fabric-flavored defaults: ``deterministic=False`` and,
for a Command or Action base, ``mutates={0}``. Both are overridable through
``attributes`` when the caller wraps a pure host method that should fold.

The ``method_*`` descriptors are class-body sugar, one per base so the effect
kind is always named at the declaration site. Each builds its atom once via
``MethodFactory`` and, on access, returns a callable that instantiates the
atom with the receiver Ref in slot 0. Class access resolves the Ref from
``objtype()``; instance access targets that Ref. A yielding variant wraps the
result in ``form``; a command variant (``form is None``) returns the raw
Command.

Any zero-arg-constructible Ref class works as the receiver - ``FabricRef``
subclasses are the common case, but nothing structural limits it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from nu.lang.kinds import Action, Command, ScalarAction, ScalarQuery

from .core import InteractionFactory


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.forms import Form
    from nu.lang.nu import Nu


__all__ = [
    "MethodFactory",
    "method_action",
    "method_command",
    "method_query",
]


B = TypeVar("B", bound="Nu")


def MethodFactory(  # noqa: N802 -- a class factory; reads as a class at the call site
    base: type[B],
    name: str,
    method_name: str,
    *,
    propagate_sentinels: bool = True,
    **attributes: object,
) -> type[B]:
    """Build an atom class that calls ``method_name`` on the slot-0 receiver.

    Thin fabric-flavored ``InteractionFactory``: the built callable is
    ``getattr(receiver, method_name)(*args, **kwargs)``, with the receiver
    resolved from slot 0 and the call arguments from slots 1... ``base``
    carries the effect semantics (``ScalarQuery`` read, ``ScalarAction`` /
    ``Command`` write). ``deterministic`` defaults False (an external method
    call never folds) and - for a Command or Action base - ``mutates``
    defaults to slot 0, both overridable through ``attributes``.
    """

    def dispatch(receiver: object, *args: object, **kwargs: object) -> object:
        return getattr(receiver, method_name)(*args, **kwargs)

    if issubclass(base, (Command, Action)):
        attributes.setdefault("mutates", frozenset({0}))
    attributes.setdefault("deterministic", False)
    return InteractionFactory(
        base, name, dispatch, propagate_sentinels=propagate_sentinels, **attributes
    )


class _MethodDescriptor:
    """Class-body descriptor behind the ``method_*`` variants.

    Builds its atom class once (via ``MethodFactory``) when the owning class
    names it, then on access returns a callable that instantiates the atom
    with the receiver Ref in slot 0. Class access (``Owner.slot()``) resolves
    the receiver from ``objtype()``; instance access (``ref.slot()``) targets
    that Ref. Any zero-arg-constructible Ref class works - ``FabricRef``
    subclasses are the common case, but nothing structural limits it.
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

    def __get__(self, obj: Nu | None, objtype: type[Nu] | None = None) -> Callable:
        ref = obj if obj is not None else objtype()
        atom, form = self._atom, self._form

        def call(*args: object, **kwargs: object) -> Nu:
            node = atom(ref, *args, **kwargs)
            return form(node) if form is not None else node

        return call


def method_query(
    form: type[Form], name: str | None = None, **attributes: object
) -> _MethodDescriptor:
    """Declare a pure external read on a receiver class.

    Builds a ``ScalarQuery`` (slot 0 READ) that yields the method's return
    value wrapped in ``form`` - reading external state without mutating the
    receiver fabric; non-determinism is carried by ``deterministic=False``,
    not by faking a write. Usage: ``slot = method_query(Int, "getSlot")``.
    """
    return _MethodDescriptor(ScalarQuery, form, name, **attributes)


def method_action(
    form: type[Form], name: str | None = None, **attributes: object
) -> _MethodDescriptor:
    """Declare an effectful call that yields a value.

    Builds a ``ScalarAction`` (slot 0 WRITE) that mutates the receiver
    fabric and yields the method's return value wrapped in ``form``; calls
    to one receiver serialize.
    Usage: ``send = method_action(Str, "sendTransaction")``.
    """
    return _MethodDescriptor(ScalarAction, form, name, **attributes)


def method_command(name: str | None = None, **attributes: object) -> _MethodDescriptor:
    """Declare an effectful call that yields nothing.

    Builds a ``Command`` (slot 0 WRITE) run for its effect. It has no value
    to type, so it takes no Form and returns the raw Command - like
    ``io.print``. Usage: ``ping = method_command("ping")``.
    """
    return _MethodDescriptor(Command, None, name, **attributes)
