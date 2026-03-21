"""Virtuals storage Resources - hierarchical composables Resources for virtuals.

Uses multiple inheritance: Resource IS the wrapped object.
No delegation wiring needed.

Chain: CodecResource -> InMemoryStorageResource -> NavigatorResource

Usage:
    spec = NavigatorSpec(
        storage_resource=InMemoryStorageSpec(
            codec_resource=CodecSpec()
        )
    )

    async with Runtime() as runtime:
        nav = await runtime.create(spec)
        with nav.transaction() as tx:
            tx.root["key"] = "value"
"""

from __future__ import annotations

import attrs
from composables import Attach, Resource, ResourceSpec
from virtuals import Navigator
from virtuals._backends.storages.mem import InMemoryStorage
from virtuals.tkv.codec.codec import Codec
from virtuals.views import DictView


__all__ = [
    "CodecResource",
    "CodecSpec",
    "InMemoryStorageResource",
    "InMemoryStorageSpec",
    "NavigatorResource",
    "NavigatorSpec",
]


# ============================================================================
# Codec
# ============================================================================


class CodecResource(Resource, Codec):
    """Resource that IS a Codec."""

    spec: CodecSpec

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init Codec from spec's key/value codec classes."""
        Codec.__init__(self, self.spec.key_codec_cls, self.spec.value_codec_cls)


@attrs.define(frozen=True, slots=True, kw_only=True)
class CodecSpec(ResourceSpec):
    """Spec for CodecResource."""

    factory: type = CodecResource
    name: str = "codec"

    key_codec_cls: type = attrs.field()
    value_codec_cls: type = attrs.field()

    @key_codec_cls.default
    def _default_key_codec(self) -> type:
        from virtuals._backends.key_codecs import StringKeyCodec

        return StringKeyCodec

    @value_codec_cls.default
    def _default_value_codec(self) -> type:
        from virtuals.codecs.passthrough import PassthroughCodec

        return PassthroughCodec


# ============================================================================
# Storage
# ============================================================================


class InMemoryStorageResource(Resource, InMemoryStorage):
    """Resource that IS an InMemoryStorage."""

    spec: InMemoryStorageSpec
    codec_resource = Attach()

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init storage with attached codec and open it."""
        InMemoryStorage.__init__(self, codec=self.codec_resource)
        self.open()

    async def cleanup(self) -> None:
        """Close storage."""
        self.close()


@attrs.define(frozen=True, slots=True, kw_only=True)
class InMemoryStorageSpec(ResourceSpec):
    """Spec for InMemoryStorageResource."""

    factory: type = InMemoryStorageResource
    name: str = "storage"

    codec_resource: CodecSpec = attrs.Factory(CodecSpec)


# ============================================================================
# Navigator
# ============================================================================


class NavigatorResource(Resource, Navigator):
    """Resource that IS a Navigator. transaction(), snapshot() work directly."""

    spec: NavigatorSpec
    storage_resource = Attach()

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init Navigator with attached storage (already opened by composables)."""
        Navigator.__init__(self, self.storage_resource, self.spec.root_view)
        self._opened = True


@attrs.define(frozen=True, slots=True, kw_only=True)
class NavigatorSpec(ResourceSpec):
    """Spec for NavigatorResource."""

    factory: type = NavigatorResource
    name: str = "navigator"

    storage_resource: InMemoryStorageSpec = attrs.Factory(InMemoryStorageSpec)
    root_view: type = DictView
