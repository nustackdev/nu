"""Ray fabric resources: ``RayCluster`` and ``RayService``.

``RayCluster`` connects to (or starts) a ray cluster and tears down its own
init on cleanup. ``RayService`` spawns one ``_RayServiceActor`` per bracket
and holds it live for the body's duration - the parent side of the remote
Nu execution.

Both implement the async resource lifecycle (``asetup`` / ``acleanup``) so
they slot straight into ``Provide`` / ``ProvideList`` / ``ProvideDict`` and
tear down LIFO with the rest of the tree.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import ray


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from nu.lang.runtime import Context
    from nu.spans.bracket import _LifecycleBracket


__all__ = ["RayCluster", "RayService"]


class RayCluster:
    """A handle on a ray cluster; provisions the local ``ray.init`` if needed.

    On ``setup``: if ``ray.is_initialized()`` is already true (someone else
    already brought the cluster up), the cluster is used as-is and
    ``cleanup`` is a no-op. Otherwise ``ray.init(address, **kwargs)`` runs
    and ``cleanup`` calls ``ray.shutdown()``.

    Sync and async both supported: ``ray.init`` / ``ray.shutdown`` are
    blocking sync calls, so ``setup`` / ``cleanup`` carry the whole body and
    ``asetup`` / ``acleanup`` are thin shims over them. Either runner works.

    Typical use in the tree::

        Provide(RayCluster, {"address": "auto"},
            ProvideList(RayService, [...], body),
        )
    """

    def __init__(
        self,
        address: str | None = "auto",
        *,
        ignore_reinit_error: bool = True,
        **init_kwargs: object,
    ) -> None:
        self.address = address
        self.ignore_reinit_error = ignore_reinit_error
        self.init_kwargs = init_kwargs
        self._owns_init = False

    def setup(self, ctx: Context) -> None:
        """Bring ray up if not already; track ownership for teardown."""
        if ray.is_initialized():
            return
        ray.init(
            address=self.address,
            ignore_reinit_error=self.ignore_reinit_error,
            **self.init_kwargs,
        )
        self._owns_init = True

    def cleanup(self) -> None:
        """Shut ray down only if we brought it up."""
        if self._owns_init:
            with contextlib.suppress(Exception):
                ray.shutdown()
            self._owns_init = False

    async def asetup(self, ctx: Context) -> None:
        """Async shim: setup is sync work."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async shim: cleanup is sync work."""
        self.cleanup()


class RayService:
    """A remote Nu execution service backed by a ``_RayServiceActor``.

    On ``setup`` / ``asetup``: spawn a ray actor (optionally pinned to a
    named node with resource / CPU / GPU constraints) and initialize its
    ``Context`` from ``init`` (a lifecycle bracket, typically ``With(...)``)
    or ``ctx_builder`` (a callable). ``aexecute(tree, attrs=None)`` routes
    to the actor. On ``cleanup`` / ``acleanup``: graceful shutdown, then
    ``ray.kill``.

    Sync and async both supported. The sync path uses ``ray.get(ref)`` to
    resolve actor ObjectRefs (blocking); the async path keeps ``await ref``
    so drivers can do other work while the actor future is in flight.
    Fleets can boot in parallel via ``ProvideDict(..., parallel=True)``.

    ``init`` is a ``_LifecycleBracket`` shipped to the actor. The actor
    enters its ``_aopen(Context())`` on start and holds the resulting
    Context live for the actor's lifetime; on shutdown the bracket tears
    down LIFO. Use ``With(*brackets)`` to compose multiple ``Provide``
    stacks.

    ``ctx_builder`` is an alternative: a callable returning a Context (or
    an awaitable). Pass exactly one of ``init`` or ``ctx_builder``.

    Actor options are pass-through: ``node``, ``actor_name``, ``num_cpus``,
    ``num_gpus``, ``max_restarts``, ``lifetime`` all forward to
    ``_RayServiceActor.options(**opts).remote()``.
    """

    def __init__(
        self,
        ctx_builder: Callable[[], Context | Awaitable[Context]] | None = None,
        *,
        init: _LifecycleBracket | None = None,
        node: str | None = None,
        actor_name: str | None = None,
        num_cpus: float | None = None,
        num_gpus: float | None = None,
        max_restarts: int = 0,
        lifetime: str | None = None,
    ) -> None:
        if init is not None and ctx_builder is not None:
            raise TypeError("RayService accepts either init= or ctx_builder=, not both")
        self.ctx_builder = ctx_builder
        self.init = init
        self.node = node
        self.actor_name = actor_name
        self.num_cpus = num_cpus
        self.num_gpus = num_gpus
        self.max_restarts = max_restarts
        self.lifetime = lifetime
        self._actor: object | None = None

    def _options(self) -> dict[str, object]:
        options: dict[str, object] = {}
        if self.node is not None:
            options["resources"] = {f"node:{self.node}": 1}
        if self.actor_name is not None:
            options["name"] = self.actor_name
        if self.num_cpus is not None:
            options["num_cpus"] = self.num_cpus
        if self.num_gpus is not None:
            options["num_gpus"] = self.num_gpus
        if self.max_restarts != 0:
            options["max_restarts"] = self.max_restarts
        if self.lifetime is not None:
            options["lifetime"] = self.lifetime
        return options

    def setup(self, ctx: Context) -> None:
        """Spawn the actor and block on its start via ``ray.get``."""
        from ._actor import _RayServiceActor

        self._actor = _RayServiceActor.options(**self._options()).remote()
        ray.get(self._actor.start.remote(self.init, self.ctx_builder))

    def cleanup(self) -> None:
        """Graceful shutdown via ``ray.get`` then ``ray.kill``."""
        if self._actor is None:
            return
        with contextlib.suppress(Exception):
            ray.get(self._actor.shutdown.remote())
        with contextlib.suppress(Exception):
            ray.kill(self._actor)
        self._actor = None

    async def asetup(self, ctx: Context) -> None:
        """Async path: await the actor's remote start so the driver stays free."""
        from ._actor import _RayServiceActor

        self._actor = _RayServiceActor.options(**self._options()).remote()
        await self._actor.start.remote(self.init, self.ctx_builder)

    async def aexecute(self, tree: object, attrs: dict | None = None) -> object:
        """Ship ``tree`` to the actor and await its result."""
        return await self._actor.aexecute.remote(tree, attrs)

    async def acleanup(self) -> None:
        """Async path: await graceful shutdown so the driver stays free."""
        if self._actor is None:
            return
        with contextlib.suppress(Exception):
            await self._actor.shutdown.remote()
        with contextlib.suppress(Exception):
            ray.kill(self._actor)
        self._actor = None
