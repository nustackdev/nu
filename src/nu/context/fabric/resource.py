"""``Resource``: anything with an optional setup / cleanup lifecycle.

Both sync (``setup`` / ``cleanup``) and async (``asetup`` / ``acleanup``)
methods are optional. A ``Provide`` bracket calls what the resource provides;
in the async runtime it prefers the async variants and falls back to sync.
No polymorphism is required - a resource with only sync methods works in the
async runtime for free, an async-only resource works in the async runtime.

``setup`` receives the *outer* ctx - everything bound by enclosing ``Provide``
brackets is already visible. That is the dependency-injection channel: an
inner resource reads its deps from ctx during its own setup, which is
guaranteed to run *after* every enclosing ``Provide`` has bound.

Example::

    class Codec:
        def __init__(self, kind): self.kind = kind
        def setup(self, ctx): ...

    class Storage:
        def __init__(self, path): self.path = path
        def setup(self, ctx):
            self.codec = ctx.get(Codec)           # DI happens here
            self.db = open(self.path, codec=self.codec)
        def cleanup(self):
            self.db.close()

    app = Provide(Codec, {"kind": "json"},
        Provide(Storage, {"path": "/data"}, body),
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["Resource"]


@runtime_checkable
class Resource(Protocol):
    """A thing with an optional setup / cleanup lifecycle.

    Sync + async methods are all optional; implement whichever fits. The
    ``Provide`` bracket picks the async variant when running under the async
    runtime and one is defined, else falls back to sync.
    """

    def setup(self, ctx: Context) -> None: ...
    def cleanup(self) -> None: ...
    async def asetup(self, ctx: Context) -> None: ...
    async def acleanup(self) -> None: ...
