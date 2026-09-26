"""Presets over ``nustd.valkey``: the bracket that brings a server up, and its address.

``server(data_dir)`` is the ``Provide`` a host puts at the top of its tree.
``url_for(data_dir)`` is the address that server will listen on, computed
without starting anything, so the kv stack that talks to it can be built in
the same ``With``, and a worker process can build the same URL on its own::

    d = ".nu/valkey"
    app = nu.With(
        nustd.valkey.server(d),
        nustd.kv.sqlite_navigator_redis(".nu/kv.sqlite", redis_url=nustd.valkey.url_for(d)),
        body=program,
    )

``With`` opens its brackets in order, so the server is answering before the
kv stack's Redis publisher and observer connect, and it is stopped after they
have closed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.fabric import Provide

from .resources import ValkeyServer, socket_path_for, url_for


if TYPE_CHECKING:
    import os
    from collections.abc import Sequence


__all__ = ["server", "socket_path_for", "url_for"]


def server(
    data_dir: str | os.PathLike[str],
    *,
    socket_path: str | None = None,
    logfile: str | None = "valkey.log",
    config: dict[str, object] | None = None,
    ready_timeout: float = 10.0,
    grace: float = 2.0,
    watchdog: bool = True,
    tags: Sequence[object] = (),
) -> Provide:
    """Brings up a private Valkey server for ``data_dir`` for the body's duration.

    Args:
        data_dir: the directory the server owns: config, pid file, log.
        socket_path: an explicit unix socket path instead of the one derived
            from ``data_dir``. Pass the same one to ``url_for``.
        logfile: the server log, relative to ``data_dir`` unless absolute.
            None discards it.
        config: extra Valkey directives applied over the defaults.
        ready_timeout: how long setup waits for the server to answer.
        grace: SIGTERM to SIGKILL escalation window, on stop and on reap.
        watchdog: stop the server if this process dies without cleanup.
        tags: tags for the binding, so two servers can be told apart.

    Notes:
        - No persistence, no TCP port: a unix socket only.
        - A server a crashed owner left in the same dir is reaped first.

    Yields:
        A ``Provide`` bracket binding the ``ValkeyServer``.

    Example:
        nu.With(nustd.valkey.server(".vk"), body=program)
    """
    kwargs = {
        "data_dir": data_dir,
        "socket_path": socket_path,
        "logfile": logfile,
        "config": config,
        "ready_timeout": ready_timeout,
        "grace": grace,
        "watchdog": watchdog,
    }
    return Provide(ValkeyServer, kwargs, tags=tuple(tags))
