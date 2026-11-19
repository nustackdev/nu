"""Raise: raise an exception at run time.

Nu's Sort taxonomy has no bare "effect" sort. A Command must declare a
mutation (the ``command_has_write`` law), and raising touches no fabric --
so Raise sits in the Control seat instead. A Control is a Flow that composes
Commands under Query parameters; Raise takes two value parameters (the
message and the exception class) and no body slots. That leaves the sort
semantics clean:

- ``Sort.CONTROL`` is a subsort of ``Sort.FLOW``, so a ``Raise`` slots into
  any Flow body position (an ``IfDo`` body, a ``Sequential`` arm, ...).
- The param slots (slot 0, the msg; slot 1, the exception class) are
  yielding -- satisfies ``control_param_yielders``.
- No body slots, so ``flow_body_is_mutator`` is trivially satisfied.

Wire-up:

- ``exc_cls`` is a child: nothing reads it before the raise runs, so it can
  be computed like the message (an exception class picked by a lookup, say).
  A plain class is checked at construction, a computed one when it runs.
- ``msg`` is any Nu expression yielding a value (typically a str). A NULL
  message still raises, though the exception cannot render it as text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Control, Nu


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["Raise", "raise_"]


class Raise(Control):
    """Raise ``exc_cls(msg)`` at run time.

    Args:
        msg: any Nu expression yielding a value (typically a str).
        exc_cls: the exception class to raise, or any Nu yielding one.

    Notes:
        - A leaf Control: children ``[msg, exc_cls]``, both param slots, no
          body slots, so ``flow_body_is_mutator`` is trivially satisfied.
        - ``exc_cls`` is a child, evaluated on every run: a plain class is
          checked here, a computed one when it runs.
        - A raise is never skipped.

    Yields:
        Never returns normally; raises ``exc_cls(msg)``.

    Example:
        >>> try:
        ...     nu.run(nu.raise_(ValueError, "boom"))
        ... except ValueError as e:
        ...     print(e)
        boom
    """

    _param_slots = Declared(value=frozenset({0, 1}), name="param_slots")

    def __init__(self, msg: Nu, *, exc_cls: type[BaseException] | Nu = RuntimeError) -> None:
        if not isinstance(exc_cls, Nu):
            _exc_class(exc_cls)
        super().__init__(msg, exc_cls)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        msg_t, exc_t = children

        def thunk(rt: Runtime) -> None:
            msg = msg_t(rt)
            raise _exc_class(exc_t(rt))(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        msg_t, exc_t = children

        async def athunk(rt: Runtime) -> None:
            msg = await msg_t(rt)
            raise _exc_class(await exc_t(rt))(msg)

        return athunk


def _exc_class(value: object) -> type[BaseException]:
    """``value`` as the class a Raise raises.

    Raises:
        TypeError: ``value`` is not an exception class.
    """
    if not (isinstance(value, type) and issubclass(value, BaseException)):
        msg = f"Raise: exc_cls must be an exception class, got {value!r}"
        raise TypeError(msg)
    return value


def raise_(exc_cls: type[BaseException] | Nu, msg: object) -> Raise:
    """Build a ``Raise`` node. Wrap in ``IfDo`` to gate.

    Args:
        exc_cls: the exception type to raise, or any Nu yielding one.
        msg: any Nu expression yielding a value - a string literal, a
            ``Str(...)``, string concat, or a formatting host callable.
    """
    return Raise(msg, exc_cls=exc_cls)
