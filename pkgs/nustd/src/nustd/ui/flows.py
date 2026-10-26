"""Program flows -- the two terms a ui program is framed by: ``boot`` and ``route``.

A ui program draws everything itself, so the host only renders the tree.
``boot`` starts a tab from nothing and brings up what is always there (the
title, the History, a nav bar). ``route`` decides what else shows, from where
the page is: it listens to a HistoryRef, matches the pathname and runs that
branch, a plain Nu term. A branch is usually ``ref.showing(work)``: the page
comes up when the route arrives and goes when it leaves.

    class App(nu.Shape):
        title = nustd.ui.TitleRef.slot()
        history = nustd.ui.HistoryRef.slot()
        nav = Nav.slot(variant="horizontal")
        movies = Movies.slot()
        detail = Detail.slot()

    program = nustd.ui.boot(App.title, App.history, App.nav) >> nustd.ui.route(
        App.history,
        {
            "/": App.movies.showing(movies_work),
            "/detail": App.detail.showing(detail_work),
        },
        fallback=not_found,
    )

Render order is the order nodes reach the tree. ``boot`` pins the ones it is
given, in order, and a node the program first writes later lands after them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
from nustd.ui.core import Clear
from nustd.ui.refs.structural import RoutePath, trim_slash


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.lang import Nu
    from nustd.ui.core import Ref
    from nustd.ui.refs import HistoryRef


__all__ = ["boot", "route"]


def boot(*refs: Ref) -> Nu:
    """Start this tab's tree over, then bring ``refs`` up as declared, in order.

    The clear goes first and down this connection's socket alone: a reconnect
    gets a fresh session with none of the old one's nodes, and whatever the
    browser still drew from before would otherwise stay. Then one ``init`` per
    ref, so each is on screen, with every slot its Shape declares, before
    anything writes, and the root lists them in this order. The browser shows
    "waiting for the tree..." until something lands, so this goes at the head
    of the program::

        program = nustd.ui.boot(App.title, App.history, App.home) >> work

    A ref left out still shows the first time anything writes to it, after
    the ones given here.
    """
    out: Nu = Clear()
    for ref in refs:
        out = out >> ref.init()
    return out


def route(
    history: HistoryRef,
    branches: Mapping[str, Nu],
    fallback: Nu | None = None,
) -> Nu:
    """Run the branch the page's pathname names, and switch when it moves.

    Matches the pathname exactly, a trailing slash aside ("/feed/" is
    "/feed"), the same rule the kit lights a NavItem by. The first run is
    straight away, for wherever the page already is; after that, every move
    that changes the pathname cancels the running branch, waits for it to
    unwind (its ``finally_``, which is where ``showing`` takes its page away),
    and starts the one the new pathname names. ``fallback`` runs when no
    branch does; None runs nothing.

    The query, the hash and the state are the branch's. A move that only
    touches them (``set_query`` on a filter, say) does not rerun anything: a
    branch that follows its query reads ``history.query()`` and listens to
    ``history.on_change()`` itself.

    Never returns. A branch that finishes leaves the route waiting for the
    next move; one that raises ends it, and the error propagates.

    Args:
        history: the HistoryRef the route follows. It has to be on screen to
            hear moves, so it goes in ``boot``.
        branches: pathname to branch, checked in order.
        fallback: what runs on a pathname no branch names.
    """
    cases: dict[str, Nu] = {}
    for path, body in branches.items():
        key = trim_slash(path)
        if not key.startswith("/"):
            msg = f"route: a branch path starts with '/', got {path!r}"
            raise ValueError(msg)
        if key in cases:
            msg = f"route: {path!r} names the same path as another branch"
            raise ValueError(msg)
        cases[key] = body
    return nu.ReactLatest(
        history.on_path_change(),
        nu.SwitchDo(RoutePath(history), cases, default=fallback),
        initial=True,
    )
