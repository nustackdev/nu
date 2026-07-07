"""Raise: raise an exception at run time.

Nu's Sort taxonomy has no bare "effect" sort. A Command must declare a
mutation (the ``command_has_write`` law), and raising touches no fabric --
so Raise sits in the Control seat instead. A Control is a Flow that composes
Commands under Query parameters; Raise takes a single value parameter (the
message) and no body slots. That leaves the sort semantics clean:

- ``Sort.CONTROL`` is a subsort of ``Sort.FLOW``, so a ``Raise`` slots into
  any Flow body position (an ``IfDo`` body, a ``Sequential`` arm, ...).
- The param slot (slot 0, the msg) is yielding -- satisfies
  ``control_param_yielders``.
- No body slots, so ``flow_body_is_mutator`` is trivially satisfied.

Wire-up:

- ``exc_cls`` is a plain Python class captured in the atom's payload -- the
  exception type is a structural detail of the tree, not run-time data.
- ``msg`` is any Nu expression yielding a value (typically a str). If the
  message resolves to a sentinel (``EMPTY`` / ``INVALID``) the raise is
  skipped -- "the condition is not yet ready", not "raise something
  obscured".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["Raise", "raise_"]


class Raise(Control):
    """Raise ``exc_cls(msg)`` at run time. A leaf Control -- one param slot
    (the msg), no body slots."""

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def __init__(self, msg: Nu, *, exc_cls: type[BaseException] = RuntimeError) -> None:
        super().__init__(msg)
        self._payload["exc_cls"] = exc_cls

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (msg_t,) = children
        exc_cls: type[BaseException] = self._payload["exc_cls"]

        def thunk(rt: Runtime) -> None:
            msg = msg_t(rt)
            if msg is EMPTY or msg is INVALID:
                return
            raise exc_cls(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (msg_t,) = children
        exc_cls: type[BaseException] = self._payload["exc_cls"]

        async def athunk(rt: Runtime) -> None:
            msg = await msg_t(rt)
            if msg is EMPTY or msg is INVALID:
                return
            raise exc_cls(msg)

        return athunk


def raise_(exc_cls: type[BaseException], msg: object) -> Raise:
    """Raise ``exc_cls(msg)`` at run time. Wrap in ``IfDo`` to gate.

    ``msg`` is any Nu expression yielding a value (typically a str). Use with
    a string literal, a ``StrForm(...)``, string concat, or a formatting host
    callable.
    """
    return Raise(msg, exc_cls=exc_cls)
