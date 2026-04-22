"""Functional tests for UUID ref.

Tests UUIDRef and UUIDSlot execution with real storage context.
"""

from uuid import NAMESPACE_DNS, UUID, uuid4

from nu.stdlib.uuid import UUIDI as UUIDRef


# ============================================================================
# UUID SET AND GET TESTS
# ============================================================================


class TestUUIDSetAndGet:
    """Test setting and getting UUID values through storage."""

    async def test_set_and_get_uuid(self, uuid_shape, ctx):
        """Set and retrieve a UUID value."""
        u = uuid4()
        await uuid_shape.id.store(u).aexecute(ctx)
        result = await uuid_shape.id.aexecute(ctx)
        assert result == u

    async def test_set_uuid_from_string(self, uuid_shape, ctx):
        """Set UUID from string."""
        uuid_str = "12345678-1234-5678-1234-567812345678"
        await uuid_shape.id.store(uuid_str).aexecute(ctx)
        result = await uuid_shape.id.aexecute(ctx)
        assert result == UUID(uuid_str)

    async def test_set_multiple_uuids(self, uuid_shape, ctx):
        """Set multiple UUID slots."""
        id1 = uuid4()
        id2 = uuid4()

        await uuid_shape.id.store(id1).aexecute(ctx)
        await uuid_shape.parent_id.store(id2).aexecute(ctx)

        assert await uuid_shape.id.aexecute(ctx) == id1
        assert await uuid_shape.parent_id.aexecute(ctx) == id2


# ============================================================================
# UUIDREF CONSTRUCTOR TESTS
# ============================================================================


class TestUUIDRefConstructors:
    """Test UUIDRef constructors with execution."""

    async def test_uuid4(self, ctx):
        """Create random UUID (version 4)."""
        result = await UUIDRef.uuid4().aexecute(ctx)
        assert isinstance(result, UUID)
        assert result.version == 4

    async def test_uuid1(self, ctx):
        """Create UUID from host ID and time (version 1)."""
        result = await UUIDRef.uuid1().aexecute(ctx)
        assert isinstance(result, UUID)
        assert result.version == 1

    async def test_uuid3(self, ctx):
        """Create UUID based on MD5 hash (version 3)."""
        result = await UUIDRef.uuid3(NAMESPACE_DNS, "example.com").aexecute(ctx)
        assert isinstance(result, UUID)
        assert result.version == 3

    async def test_uuid5(self, ctx):
        """Create UUID based on SHA-1 hash (version 5)."""
        result = await UUIDRef.uuid5(NAMESPACE_DNS, "example.com").aexecute(ctx)
        assert isinstance(result, UUID)
        assert result.version == 5

    async def test_from_str(self, ctx):
        """Create from string."""
        uuid_str = "12345678-1234-5678-1234-567812345678"
        result = await UUIDRef.from_str(uuid_str).aexecute(ctx)
        assert result == UUID(uuid_str)

    async def test_from_str_no_hyphens(self, ctx):
        """Create from string without hyphens."""
        uuid_str = "12345678123456781234567812345678"
        result = await UUIDRef.from_str(uuid_str).aexecute(ctx)
        assert result == UUID(uuid_str)

    async def test_from_bytes(self, ctx):
        """Create from 16 bytes."""
        uuid_bytes = b"\x12\x34\x56\x78" * 4
        result = await UUIDRef.from_bytes(uuid_bytes).aexecute(ctx)
        assert result.bytes == uuid_bytes

    async def test_from_int(self, ctx):
        """Create from 128-bit integer."""
        uuid_int = 0x12345678123456781234567812345678
        result = await UUIDRef.from_int(uuid_int).aexecute(ctx)
        assert result.int == uuid_int


# ============================================================================
# UUID COMPONENT ACCESS TESTS
# ============================================================================


class TestUUIDComponentAccess:
    """Test accessing UUID components."""

    async def test_version(self, uuid_shape, ctx):
        """Access UUID version."""
        u = await UUIDRef.uuid4().aexecute(ctx)
        await uuid_shape.id.store(u).aexecute(ctx)
        result = await uuid_shape.id.version().aexecute(ctx)
        assert result == 4

    async def test_variant(self, uuid_shape, ctx):
        """Access UUID variant."""
        u = await UUIDRef.uuid4().aexecute(ctx)
        await uuid_shape.id.store(u).aexecute(ctx)
        result = await uuid_shape.id.variant().aexecute(ctx)
        assert "RFC" in result or "specified" in result.lower()

    async def test_time(self, uuid_shape, ctx):
        """Access UUID time (for version 1)."""
        u = await UUIDRef.uuid1().aexecute(ctx)
        await uuid_shape.id.store(u).aexecute(ctx)
        result = await uuid_shape.id.time().aexecute(ctx)
        assert isinstance(result, int)
        assert result > 0

    async def test_clock_seq(self, uuid_shape, ctx):
        """Access UUID clock sequence (for version 1)."""
        u = await UUIDRef.uuid1().aexecute(ctx)
        await uuid_shape.id.store(u).aexecute(ctx)
        result = await uuid_shape.id.clock_seq().aexecute(ctx)
        assert isinstance(result, int)

    async def test_node(self, uuid_shape, ctx):
        """Access UUID node (for version 1)."""
        u = await UUIDRef.uuid1().aexecute(ctx)
        await uuid_shape.id.store(u).aexecute(ctx)
        result = await uuid_shape.id.node().aexecute(ctx)
        assert isinstance(result, int)


# ============================================================================
# UUID CONVERSION TESTS
# ============================================================================


class TestUUIDConversions:
    """Test UUID conversions."""

    async def test_hex(self, uuid_shape, ctx):
        """Convert to hex string."""
        uuid_str = "12345678-1234-5678-1234-567812345678"
        await uuid_shape.id.store(UUID(uuid_str)).aexecute(ctx)
        result = await uuid_shape.id.hex().aexecute(ctx)
        assert result == "12345678123456781234567812345678"

    async def test_urn(self, uuid_shape, ctx):
        """Convert to URN string."""
        uuid_str = "12345678-1234-5678-1234-567812345678"
        await uuid_shape.id.store(UUID(uuid_str)).aexecute(ctx)
        result = await uuid_shape.id.urn().aexecute(ctx)
        assert result == "urn:uuid:12345678-1234-5678-1234-567812345678"

    async def test_bytes(self, uuid_shape, ctx):
        """Convert to bytes."""
        u = uuid4()
        await uuid_shape.id.store(u).aexecute(ctx)
        result = await uuid_shape.id.bytes().aexecute(ctx)
        assert len(result) == 16
        assert result == u.bytes

    async def test_bytes_le(self, uuid_shape, ctx):
        """Convert to bytes in little-endian order."""
        u = uuid4()
        await uuid_shape.id.store(u).aexecute(ctx)
        result = await uuid_shape.id.bytes_le().aexecute(ctx)
        assert len(result) == 16
        assert result == u.bytes_le

    async def test_int(self, uuid_shape, ctx):
        """Convert to 128-bit integer."""
        uuid_str = "12345678-1234-5678-1234-567812345678"
        await uuid_shape.id.store(UUID(uuid_str)).aexecute(ctx)
        result = await uuid_shape.id.int_().aexecute(ctx)
        assert result == 0x12345678123456781234567812345678


# ============================================================================
# UUID EQUALITY TESTS
# ============================================================================


class TestUUIDEquality:
    """Test UUID equality operations."""

    async def test_equals(self, uuid_shape, ctx):
        """Compare UUIDs for equality."""
        u = uuid4()
        await uuid_shape.id.store(u).aexecute(ctx)
        await uuid_shape.parent_id.store(u).aexecute(ctx)

        result = await uuid_shape.id.eq(uuid_shape.parent_id).aexecute(ctx)
        assert result is True

    async def test_not_equals(self, uuid_shape, ctx):
        """Compare UUIDs for inequality."""
        await uuid_shape.id.store(uuid4()).aexecute(ctx)
        await uuid_shape.parent_id.store(uuid4()).aexecute(ctx)

        result = await uuid_shape.id.ne(uuid_shape.parent_id).aexecute(ctx)
        assert result is True


# ============================================================================
# UUID DETERMINISTIC TESTS
# ============================================================================


class TestUUIDDeterministic:
    """Test UUID deterministic generation."""

    async def test_uuid3_same_input_same_output(self, ctx):
        """UUID3 with same input produces same output."""
        result1 = await UUIDRef.uuid3(NAMESPACE_DNS, "example.com").aexecute(ctx)
        result2 = await UUIDRef.uuid3(NAMESPACE_DNS, "example.com").aexecute(ctx)
        assert result1 == result2

    async def test_uuid3_different_input_different_output(self, ctx):
        """UUID3 with different input produces different output."""
        result1 = await UUIDRef.uuid3(NAMESPACE_DNS, "example.com").aexecute(ctx)
        result2 = await UUIDRef.uuid3(NAMESPACE_DNS, "other.com").aexecute(ctx)
        assert result1 != result2

    async def test_uuid5_same_input_same_output(self, ctx):
        """UUID5 with same input produces same output."""
        result1 = await UUIDRef.uuid5(NAMESPACE_DNS, "example.com").aexecute(ctx)
        result2 = await UUIDRef.uuid5(NAMESPACE_DNS, "example.com").aexecute(ctx)
        assert result1 == result2

    async def test_uuid5_different_input_different_output(self, ctx):
        """UUID5 with different input produces different output."""
        result1 = await UUIDRef.uuid5(NAMESPACE_DNS, "example.com").aexecute(ctx)
        result2 = await UUIDRef.uuid5(NAMESPACE_DNS, "other.com").aexecute(ctx)
        assert result1 != result2
