"""A tiny user app - one Shape, one nested Shape, one Service.

Stands in for "an agent was handed a bound app it did not write". It has to
be an importable module, not a class defined in a test body, because the
whole point of the Inspect atom is that it resolves a dotted path.
"""

from __future__ import annotations

import nu
import nustd.http
import nustd.mem


__all__ = ["GH", "Person", "Task"]


class Person(nu.Shape):
    """Whoever a task is assigned to."""

    name: nustd.mem.StrRef
    email: nustd.mem.StrRef


class Task(nu.Shape):
    """One unit of work on the board.

    Notes:
        - `done` is written only by the reconciler, never by the UI.
    """

    title: nustd.mem.StrRef
    priority: nustd.mem.IntRef
    owner: Person = nustd.mem.ShapeRef.slot(Person)


class GH(nu.Service):
    """The GitHub endpoints the board syncs against."""

    get_repo = nustd.http.GETRef.method("/repos/{owner}/{name}")
