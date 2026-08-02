"""Nu surface for Python's ``logging`` module.

``logging`` is a class-and-functions module: a :class:`Logger` class you get
from :func:`getLogger`, plus module-level shortcuts (``debug`` / ``info`` /
``warning`` / ``error`` / ``critical``) that fire against the root logger.
The Nu surface mirrors that shape 1-1. Call sites read identically to
Python, but every call returns a Nu ``Log`` tree instead of firing
immediately. Compose it into any bigger program::

    from nu.std import logging

    log = logging.getLogger(__name__)

    tree = (
        log.info("server started")
        >> log.warning("cache miss for %s", key)
        >> log.error("checkout failed", extra={"code": 500})
    )
    nu.run(tree)

The sink is Python's ``logging`` module itself. Its handlers, formatters,
filters, and logger hierarchy are the configuration surface. There is no
separate Nu backend to bind; users configure via ``logging.basicConfig(...)``
or attached handlers exactly the way any Python program does. That gives
free interop with the whole Python ecosystem: journald, syslog, structlog,
sentry, rotating files, ...

Two layers behind the public surface: ``interactions`` (the :class:`Log`
atom and its :class:`LoggingRef` fabric) and ``functions`` (the :class:`Logger`
class and the module-level shortcuts). Import the way you would the stdlib::

    from nu.std.logging import getLogger, info, warning, error
    import nu.std.logging as logging     # then logging.getLogger(...), ...
"""

from __future__ import annotations

from nu.std.logging.functions import (
    CRITICAL,
    DEBUG,
    ERROR,
    FATAL,
    INFO,
    NOTSET,
    WARN,
    WARNING,
    Logger,
    critical,
    debug,
    error,
    getLogger,
    info,
    log,
    warn,
    warning,
)
from nu.std.logging.interactions import LOGGING, Log, LoggingRef


__all__ = [
    "CRITICAL",
    "DEBUG",
    "ERROR",
    "FATAL",
    "INFO",
    "LOGGING",
    "NOTSET",
    "WARN",
    "WARNING",
    "Log",
    "Logger",
    "LoggingRef",
    "critical",
    "debug",
    "error",
    "getLogger",
    "info",
    "log",
    "warn",
    "warning",
]
