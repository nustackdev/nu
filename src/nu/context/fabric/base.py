"""``Fabric``: the base class of every provided fabric.

A fabric is an addressable space that resolves its own Refs and carries out
the Interactions over them: a storage handle, a cluster handle, a websocket
server, a client. ``Provide`` / ``ProvideList`` / ``ProvideDict`` install one
into ctx for a body's duration: the bracket constructs the instance, runs its
setup, binds it, and runs its cleanup on exit (LIFO across nested brackets).
The class a ``Provide`` is given must subclass ``Fabric``.

The base carries the whole lifecycle with defaults, so a fabric overrides only
what it needs:

    def setup(self, ctx): ...        # no-op by default
    def cleanup(self): ...           # no-op by default
    async def asetup(self, ctx): ... # calls setup(ctx) by default
    async def acleanup(self): ...    # calls cleanup() by default

A fabric with sync lifecycle overrides ``setup`` / ``cleanup`` and runs under
both runners. One whose lifecycle has to await overrides ``asetup`` /
``acleanup`` and sets ``async_only = True``, so the sync runner refuses it
before it is constructed instead of skipping its setup.

``setup`` receives the outer ctx - everything bound by enclosing ``Provide``
brackets is already visible. That is the dependency-injection channel: an
inner fabric reads its deps from ctx during its own setup, which is
guaranteed to run *after* every enclosing ``Provide`` has bound.

Raw ``ctx.fabrics.bind`` is not checked: anything can be bound there (a
plain dict, a protocol-typed backend).

Example::

    class Codec(Fabric):                      # no lifecycle needed
        def __init__(self, kind): self.kind = kind

    class Storage(Fabric):
        def __init__(self, path): self.path = path
        def setup(self, ctx):
            self.codec = ctx.fabrics.get(Codec)       # DI happens here
            self.db = open(self.path, codec=self.codec)
        def cleanup(self):
            self.db.close()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["Fabric"]


class Fabric:
    """The base class of a fabric that ``Provide`` installs into ctx.

    ``Provide`` / ``ProvideList`` / ``ProvideDict`` construct a subclass,
    run its setup, bind it on ctx for the body's duration, and run its
    cleanup on exit. Every lifecycle method has a default, so a subclass
    overrides only the ones it needs.

    Attributes:
        async_only: True when the fabric's lifecycle has to await (only
            ``asetup`` / ``acleanup`` do real work). The sync runner refuses
            such a fabric before constructing it.

    Notes:
        - Under ``nu.arun`` the bracket calls ``asetup`` / ``acleanup``;
          their defaults call the sync pair. Under ``nu.run`` it calls
          ``setup`` / ``cleanup``.
    """

    async_only: ClassVar[bool] = False

    def setup(self, ctx: Context) -> None:
        """Sync setup; sees the outer ``ctx``. Runs before the body starts. No-op by default."""

    def cleanup(self) -> None:
        """Sync teardown; runs after the body finishes (LIFO across nested Provides). No-op by default."""

    async def asetup(self, ctx: Context) -> None:
        """Async setup, used under the async runtime. Calls ``setup`` by default."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async teardown, used under the async runtime. Calls ``cleanup`` by default."""
        self.cleanup()
