"""Module-level surface for ``nu.std.logging``. Mirrors ``logging`` 1-1.

Two layers: the :class:`Logger` class (returned by :func:`getLogger`) and the
module-level shortcuts (:func:`debug`, :func:`info`, :func:`warning`,
:func:`warn`, :func:`error`, :func:`critical`, :func:`log`) that fire on the
root logger, exactly like the stdlib's module-level helpers.

Same API shape as Python's ``logging``::

    from nu.std import logging

    log = logging.getLogger(__name__)

    tree = (
        log.info("server started")
        >> log.warning("cache miss for %s", key)
        >> log.error("checkout failed: %s", err, extra={"code": 500})
    )
    nu.run(tree)

Only difference from Python: every call returns a Nu ``Log`` tree; it
doesn't fire until the tree is evaluated. Compose it into any bigger
program, and effect ordering keeps two logs in a ``Sequential`` in order.

The configuration surface stays fully Python: ``logging.basicConfig(...)``,
``logging.getLogger(...).addHandler(...)``, ``structlog``, ``sentry_sdk``,
journald, whatever. This module wraps the *call* side; ``logging``'s handler
machinery is the sink and needs no Nu wrapper.
"""

from __future__ import annotations

import logging as _pylogging

from nu.std.logging.interactions import Log


__all__ = [
    "CRITICAL",
    "DEBUG",
    "ERROR",
    "FATAL",
    "INFO",
    "NOTSET",
    "WARN",
    "WARNING",
    "Logger",
    "critical",
    "debug",
    "error",
    "getLogger",
    "info",
    "log",
    "warn",
    "warning",
]


# --- level constants (mirror ``logging.DEBUG`` etc for import parity) -------

DEBUG = _pylogging.DEBUG
INFO = _pylogging.INFO
WARNING = _pylogging.WARNING
WARN = _pylogging.WARNING  # stdlib alias
ERROR = _pylogging.ERROR
CRITICAL = _pylogging.CRITICAL
FATAL = _pylogging.CRITICAL  # stdlib alias
NOTSET = _pylogging.NOTSET


# --- the bound-logger class -------------------------------------------------


class Logger:
    """Bound logger. Mirrors ``logging.Logger`` on the call side.

    ``getLogger(__name__)`` at module top, then ``log.info(...)`` /
    ``log.warning(...)`` / ``log.error(...)`` at call sites. Each method
    returns a Nu ``Log`` tree carrying the bound logger name.

    Not itself a ``logging.Logger``. Users who want to configure the
    underlying Python logger (add a handler, set a level) reach for
    ``logging.getLogger(name)`` on the Python side. This is the *call*
    surface only.

    Level shortcuts ``debug`` / ``info`` / ``warning`` / ``error`` /
    ``critical`` build a ``Log`` at the matching level; ``log(level, ...)``
    takes the level as an argument. ``warn`` aliases ``warning``, ``fatal``
    aliases ``critical`` (stdlib parity).
    """

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        """The logger name this instance is bound to."""
        return self._name

    def log(
        self,
        level: int | str,
        msg: object,
        *args: object,
        extra: dict[str, object] | None = None,
    ) -> Log:
        """Build a ``Log`` at ``level``."""
        return Log(level, self._name, msg, *args, extra=extra)

    def debug(self, msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
        """Build a ``Log`` at DEBUG."""
        return Log(DEBUG, self._name, msg, *args, extra=extra)

    def info(self, msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
        """Build a ``Log`` at INFO."""
        return Log(INFO, self._name, msg, *args, extra=extra)

    def warning(self, msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
        """Build a ``Log`` at WARNING."""
        return Log(WARNING, self._name, msg, *args, extra=extra)

    # `warn` is the stdlib alias (deprecated in stdlib but universally used).
    warn = warning

    def error(self, msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
        """Build a ``Log`` at ERROR."""
        return Log(ERROR, self._name, msg, *args, extra=extra)

    def critical(self, msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
        """Build a ``Log`` at CRITICAL."""
        return Log(CRITICAL, self._name, msg, *args, extra=extra)

    # `fatal` is stdlib's alias.
    fatal = critical

    def __repr__(self) -> str:
        return f"nu.std.logging.Logger(name={self._name!r})"


def getLogger(name: str | None = None) -> Logger:  # noqa: N802 -- stdlib name
    """Return a bound :class:`Logger`. Mirrors ``logging.getLogger(name)``.

    Passing ``None`` (or omitting the argument) returns the root logger, same
    as the stdlib.
    """
    return Logger(name if name is not None else "root")


# --- module-level shortcuts (mirror ``logging.debug`` / ``logging.info`` etc.) ---
#
# In the stdlib these fire against the root logger; here they build Log
# trees against the root logger name. Identical call shape.

_root = Logger("root")


def debug(msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
    """Root-logger DEBUG shortcut."""
    return _root.debug(msg, *args, extra=extra)


def info(msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
    """Root-logger INFO shortcut."""
    return _root.info(msg, *args, extra=extra)


def warning(msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
    """Root-logger WARNING shortcut."""
    return _root.warning(msg, *args, extra=extra)


warn = warning  # stdlib alias


def error(msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
    """Root-logger ERROR shortcut."""
    return _root.error(msg, *args, extra=extra)


def critical(msg: object, *args: object, extra: dict[str, object] | None = None) -> Log:
    """Root-logger CRITICAL shortcut."""
    return _root.critical(msg, *args, extra=extra)


def log(
    level: int | str, msg: object, *args: object, extra: dict[str, object] | None = None
) -> Log:
    """Root-logger shortcut at ``level``."""
    return _root.log(level, msg, *args, extra=extra)
