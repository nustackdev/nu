"""The ``Log`` atom. One write through Python's ``logging`` module.

Every log statement in a Nu program compiles to a ``Log``. The Command
mutates the log fabric (a single ``LoggingRef`` singleton, :data:`LOGGING`) and
at eval time hands the resolved record to ``logging.getLogger(name).log(...)``.
Python's ``logging`` module IS the sink. Its handlers, formatters, filters,
and hierarchy are the configuration surface. There is no separate Nu backend
to bind: users configure via ``logging.basicConfig(...)`` or attached handlers
exactly the way any Python program does.

Slot layout is ``[LOGGING, level, logger, msg, *args]`` with the structured
``extra`` dict carried in ``_payload``. Slot 0 is declared WRITE, so effect
tracking preserves order across log statements. Two logs in a Sequential
emit in order rather than getting parallelized as pure Queries. ``*args`` are
Nu-interpolable; they participate in the ``%`` formatting of ``msg`` at
eval time, mirroring ``logging.Logger.log(level, msg, *args)``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from nu.engine.structure import Declared
from nu.lang import Command, Ref
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "LOGGING",
    "Log",
    "LoggingRef",
]


# Level names → int codes. Accepts the Python-canonical names plus the common
# ``warn`` alias; anything else defaults to INFO. Ints pass through untouched.
_LEVELS: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
    "fatal": logging.CRITICAL,
}


def _to_level(raw: object) -> int:
    """Normalize a level (int, name, or Python constant) into a logging int."""
    if isinstance(raw, int):
        return raw
    return _LEVELS.get(str(raw).lower(), logging.INFO)


# --- the log fabric Ref -----------------------------------------------------


class LoggingRef(Ref):
    """A Ref naming Python's ``logging`` module. The sink for the log fabric.

    Fixed singleton (:data:`LOGGING`). Unlike ``StdioRef`` there is no
    swappable backend: ``logging`` is a Python module-level singleton whose
    handlers are the real configuration surface. This Ref exists so
    ``Log`` can declare a slot-0 WRITE against a concrete fabric class,
    which is what the engine uses to order log statements against each other.
    """

    def _resolve_module(self) -> object:
        return logging

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return logging

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return logging

        return athunk

    def _write(self, rt: Runtime, record: tuple, nid: int) -> None:
        """Hand one resolved record to Python's ``logging`` module."""
        level, logger_name, msg, args, extra = record
        logging.getLogger(logger_name).log(level, msg, *args, extra=extra or None)

    async def _awrite(self, rt: Runtime, record: tuple, nid: int) -> None:
        """Async sibling of :meth:`_write`. ``logging`` is sync so same call."""
        level, logger_name, msg, args, extra = record
        logging.getLogger(logger_name).log(level, msg, *args, extra=extra or None)

    def __repr__(self) -> str:
        return "LoggingRef.LOGGING"


LOGGING = LoggingRef()


# --- the Log ---------------------------------------------------------


class Log(Command):
    r"""Writes one leveled record through Python's ``logging`` module.

    Children: ``[LOGGING, level, logger, msg, *args]``. ``level`` is a name
    (``"info"``, ``"warning"``, ...) or an int (``logging.INFO``); ``logger``
    is the logger name; both are children so a tree rewrite can retarget them.
    ``msg`` is the format string and ``*args`` are the ``%``-substitution
    values, resolved at eval time. Structured ``extra`` fields ride in
    :attr:`_payload` (static Python values captured at construction).

    A ``msg`` or ``arg`` that reads as an unbound sentinel drops the whole
    line, the same skip-on-EMPTY guard :class:`Print` uses. That
    keeps a log call safe against attrs that may not be populated on every
    branch.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(
        self,
        level: object,
        logger: object,
        msg: object,
        *args: object,
        extra: dict[str, object] | None = None,
    ) -> None:
        super().__init__(LOGGING, level, logger, msg, *args)
        # extra is a static Python dict; dynamic fields belong in `msg` via %-args.
        self._payload = dict(self._payload)
        self._payload["extra"] = dict(extra) if extra else {}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = cast("LoggingRef", self._children[0])
        level_thunk, logger_thunk, msg_thunk = children[1], children[2], children[3]
        arg_thunks = children[4:]
        extra: dict[str, object] = cast("dict[str, object]", self._payload["extra"])

        def thunk(rt: Runtime) -> None:
            msg = msg_thunk(rt)
            if msg is EMPTY or msg is INVALID:
                return
            args: list[object] = []
            for at in arg_thunks:
                v = at(rt)
                if v is EMPTY or v is INVALID:
                    return
                args.append(v)
            level = _to_level(level_thunk(rt))
            logger_name = str(logger_thunk(rt))
            record = (level, logger_name, msg, tuple(args), extra)
            ref._write(rt, record, rt.program.children[nid][0])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = cast("LoggingRef", self._children[0])
        level_thunk, logger_thunk, msg_thunk = children[1], children[2], children[3]
        arg_thunks = children[4:]
        extra: dict[str, object] = cast("dict[str, object]", self._payload["extra"])

        async def athunk(rt: Runtime) -> None:
            msg = await msg_thunk(rt)
            if msg is EMPTY or msg is INVALID:
                return
            args: list[object] = []
            for at in arg_thunks:
                v = await at(rt)
                if v is EMPTY or v is INVALID:
                    return
                args.append(v)
            level = _to_level(await level_thunk(rt))
            logger_name = str(await logger_thunk(rt))
            record = (level, logger_name, msg, tuple(args), extra)
            await ref._awrite(rt, record, rt.program.children[nid][0])

        return athunk
