"""Capabilities -- what a Ref can be read for and heard on, as mixins.

A Ref states what it does with the browser by the mixins it takes, so the
rules hold by structure:

- ``Emits``    -- the Ref sends notifies; ``on_event()`` hears every one.
                  The base of every event mixin.
- ``Readable`` -- the browser owns state the server can read back: the Ref
                  itself is the main read (``nu.let(..., value=slider)``), and
                  named readers read one field each (``tree.expanded()``).
- ``Changes``  -- readable state that moves: ``on_change()`` hears it
                  committed. Takes ``Readable``, so a Ref that announces a
                  change can always be read for what it changed to.
- ``Moves``    -- a value that moves while the person works it (a keystroke,
                  a drag tick): ``on_input()``.
- ``Submits``  -- a send key: ``on_submit()``.

A trigger with no state (a button's click) keeps its own small
``on_<event>`` over ``Emits``. Every ``on_<x>()`` subscribes to the wire event
``x`` and nothing else.

The mixins go before the Ref base in the class line
(``class InputLeaf(Changes, LeafRef)``), so ``Readable``'s read wins over the
base Ref's "display-only" one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from .events import CHANGE, INPUT, SUBMIT
from .interactions import Changed, ReadField


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["Changes", "Emits", "Moves", "Readable", "Submits"]


class Emits:
    """Mixin: the Ref sends notifies, each naming its event."""

    def on_event(self) -> Changed:
        """Every notify the Ref sends, whatever its event.

        The payload names it (``{event: ..., ...}``): branch on
        ``payload["event"]``. For one kind only, take its own ``on_<event>()``.
        """
        return Changed(self)  # type: ignore[arg-type]


class Readable:
    """Mixin: the browser owns state the server reads back, one round trip a read.

    Reading the Ref is the main read: what the node holds (an input's value,
    the active tab). A named reader reads one other field and is a one liner
    over ``_read``::

        def expanded(self) -> ReadField:
            return self._read("expanded")

    The main read goes through ``_lift``, a field read through
    ``_lift_field``: override either to give the raw wire value its type.
    """

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)  # type: ignore[attr-defined]

        return athunk

    #: The event that fires when a named field moves, for a field whose event
    #: is not its own name (a tree's ``expanded`` moves on ``toggle``).
    _reader_events: ClassVar[dict[str, str]] = {}

    def _read(self, field: str) -> ReadField:
        """The term that reads ``field`` off the node: what a named reader returns."""
        return ReadField(self, field)  # type: ignore[arg-type]

    def _lift_field(self, field: str, raw: object) -> object:
        """A named field's wire value as the reader returns it. As sent, by default."""
        return raw


class Changes(Readable, Emits):
    """Mixin: readable state that moves, heard committed by ``on_change()``."""

    def on_change(self) -> Changed:
        """Each committed change: blur, Enter, a quiet moment, a pick, a toggle, a release.

        Never per keystroke or drag tick: that is ``on_input()``, where the
        Ref has one.
        """
        return Changed(self, CHANGE)  # type: ignore[arg-type]


class Moves(Emits):
    """Mixin: the value moves while the person works it, heard by ``on_input()``."""

    def on_input(self) -> Changed:
        """Each move of the value: a keystroke, a drag tick.

        Every tick arrives; slowing it down is the program's call
        (``nu.Debounce``, ``nu.Throttle``). The commit is ``on_change()``.
        """
        return Changed(self, INPUT)  # type: ignore[arg-type]


class Submits(Emits):
    """Mixin: the Ref has a send key, heard by ``on_submit()``."""

    def on_submit(self) -> Changed:
        """The person asked to send: Enter, or a multi-line field's send key.

        The payload is ``{event: "submit", value}``, the value sent: read it
        there (``lambda sub: save(sub["value"])``), not off the input, which
        ``clear_on_submit`` has emptied by then.
        """
        return Changed(self, SUBMIT)  # type: ignore[arg-type]
