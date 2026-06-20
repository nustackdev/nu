"""IO atoms: Python's console and file builtins.

Maps Python's effectful IO builtins onto Nu. This file crosses sorts: a write
that yields nothing is a Command, a read or open that yields a value is an
Action (effect + yield in one atom).

Builtins to cover (Python -> Nu):
- ``print`` -> ``Print`` (write to stdout, yields nothing -> Command)
- ``input`` -> ``Input`` (read a line, mutate stdin position + yield -> Action)
- ``open`` -> ``Open`` (open a file, side effect + yield the handle -> Action)

Sorts: Command (C) for ``Print``, ScalarAction (A) for ``Input`` / ``Open``.

Every atom declares ``mutates``: slot 0 holds the Ref it writes through. For IO
that Ref is an **IO fabric Ref** (the stdio fabric, see ``src/nu/stdio``), not
an in-memory value Ref - ``Print`` writes through the stdout fabric, ``Input``
through stdin, ``Open`` through the filesystem fabric. The effect is attributed
exactly like any Command write (slot 0 in write role), so the language tracks it
today; full evaluation lands once the stdio fabric is wired, hence these atoms
are declared **structurally** (no ``eval`` / ``aeval``). Async file IO (an
async ``Open`` twin) can follow once the fabric exposes it.

v1 reference: ``src/nu/commands/io.py`` (Print, Log) and ``src/nu/stdio/ops.py``
(StdioWrite, StdioRead, StdioFlush).
"""

from __future__ import annotations

from nu2.engine.structure import Declared
from nu2.lang import Command, ScalarAction


__all__ = ["Input", "Open", "Print"]


class Print(Command):
    """Writes the values in slots 1.. to the stdout fabric Ref in slot 0.

    Python's ``print``. A Command: it mutates the stdout fabric and yields
    nothing. Slot 0 is the IO Ref it writes through (the stdout fabric, not an
    in-memory value Ref); every other slot binds in read role.
    """

    mutates = Declared(value=frozenset({0}))


class Input(ScalarAction):
    """Reads one line from the stdin fabric Ref in slot 0 and yields it.

    Python's ``input``. A ScalarAction: it mutates the stdin fabric (advances
    the read position) and yields the line read. Slot 0 is the IO Ref it reads
    through (the stdin fabric, not an in-memory value Ref); any prompt slot
    binds in read role.
    """

    mutates = Declared(value=frozenset({0}))


class Open(ScalarAction):
    """Opens the path in slots 1.. on the filesystem fabric Ref in slot 0.

    Python's ``open``. A ScalarAction: it mutates the filesystem fabric (opens
    a handle) and yields the file handle. Slot 0 is the IO Ref it acts through
    (the filesystem fabric, not an in-memory value Ref); the path and mode slots
    bind in read role. An async ``Open`` twin can land once the fabric exposes
    async file IO.
    """

    mutates = Declared(value=frozenset({0}))
