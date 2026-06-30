"""Nu surface for Python's ``datetime`` module.

Mirrors ``datetime`` 1-1: the classes ``date`` / ``datetime`` / ``time`` /
``timedelta`` / ``timezone`` are Forms. ``datetime`` has no module-level
functions, so there is no ``functions`` layer - just ``forms`` (the classes)
and ``interactions`` (the constructor atoms; method calls use the shared
``nu.lang.MethodCallQuery``). Import it like the stdlib::

    from nu.std.datetime import date, timedelta
    import nu.std.datetime as datetime    # datetime.date.today(), ...
"""

from __future__ import annotations

from nu.std.datetime.forms import date, datetime, time, timedelta, timezone


__all__ = ["date", "datetime", "time", "timedelta", "timezone"]
