"""``Fabric``: the base class of a declared nu fabric, with an optional lifecycle.

A fabric is a long-lived, typed piece of state a program reaches through the
Context: a storage handle, a cluster handle, a websocket server, a client.
``Provide`` / ``ProvideList`` / ``ProvideDict`` install one into ctx for a
body's duration: the bracket constructs the instance, runs its setup, binds
it, and runs its cleanup on exit (LIFO across nested brackets).

Subclassing ``Fabric`` is a choice, not a requirement: ``Provide`` takes any
class. A plain class is only bound and unbound, a context manager is entered
and exited. Subclass ``Fabric`` to declare a class as a nu fabric, or for a
lifecycle that sees the Context (the dependency-injection channel below) or
has to be refused under the sync runner.

The base carries the whole lifecycle with defaults, so a fabric overrides only
what it needs:

    def setup(self, ctx): ...        # no-op by default
    def cleanup(self): ...           # no-op by default
    async def asetup(self, ctx): ... # calls setup(ctx) by default
    async def acleanup(self): ...    # calls cleanup() by default

A fabric with sync lifecycle overrides ``setup`` / ``cleanup`` and runs under
both runners. One whose lifecycle has to await overrides ``asetup`` /
``acleanup`` and sets ``async_only = True``, so the sync runner refuses it
before it is constructed instead of skipping its setup. One that overrides
``asetup`` (or ``acleanup``) without the sync twin is refused the same way,
marked or not.

``setup`` receives the outer ctx - everything bound by enclosing ``Provide``
brackets is already visible. That is the dependency-injection channel: an
inner fabric reads its deps from ctx during its own setup, which is
guaranteed to run *after* every enclosing ``Provide`` has bound.

Example::

    class Codec(Fabric):                      # no lifecycle needed
        def __init__(self, kind): self.kind = kind

    class Storage(Fabric):
        def __init__(self, path): self.path = path
        def setup(self, ctx):
            self.codec = ctx.get(Codec)       # DI happens here
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
    """The base class of a declared nu fabric, with an optional lifecycle.

    ``Provide`` / ``ProvideList`` / ``ProvideDict`` construct a subclass,
    run its setup, bind it on ctx for the body's duration, and run its
    cleanup on exit. Every lifecycle method has a default, so a subclass
    overrides only the ones it needs. ``Provide`` takes classes that are not
    fabrics too; this base is for the ones whose lifecycle sees the Context.

    Attributes:
        async_only: True when the fabric's lifecycle has to await (only
            ``asetup`` / ``acleanup`` do real work). The sync runner refuses
            such a fabric before constructing it.

    Notes:
        - Under ``nu.arun`` the bracket calls ``asetup`` / ``acleanup``;
          their defaults call the sync pair. Under ``nu.run`` it calls
          ``setup`` / ``cleanup``, and refuses a subclass that overrides
          ``asetup`` / ``acleanup`` but not the matching sync method.
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
