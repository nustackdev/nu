"""Unit tests for UUID type.

Tests for:
- UUIDType (constructors, operations, methods)
"""

from uuid import NAMESPACE_DNS

from everybase.type.uuid import UUIDType
from everyterm.ops import FuncCallOp
from everyterm.types import BytesType, IntType, StrType


# =============================================================================
# UUIDTYPE CONSTRUCTION TESTS
# =============================================================================


class TestUUIDTypeConstruction:
    """UUIDType construction tests."""

    def test_uuid4(self):
        """Create random UUID (version 4)."""
        ut = UUIDType.uuid4()
        assert isinstance(ut, UUIDType)
        assert isinstance(ut.source, FuncCallOp)

    def test_uuid1(self):
        """Create UUID from host ID and time (version 1)."""
        ut = UUIDType.uuid1()
        assert isinstance(ut, UUIDType)

    def test_uuid1_with_node(self):
        """Create UUID with specific node."""
        ut = UUIDType.uuid1(node=0x0123456789AB)
        assert isinstance(ut, UUIDType)

    def test_uuid1_with_node_and_clock_seq(self):
        """Create UUID with node and clock sequence."""
        ut = UUIDType.uuid1(node=0x0123456789AB, clock_seq=0x1234)
        assert isinstance(ut, UUIDType)

    def test_uuid3(self):
        """Create UUID based on MD5 hash (version 3)."""
        ut = UUIDType.uuid3(NAMESPACE_DNS, "example.com")
        assert isinstance(ut, UUIDType)

    def test_uuid5(self):
        """Create UUID based on SHA-1 hash (version 5)."""
        ut = UUIDType.uuid5(NAMESPACE_DNS, "example.com")
        assert isinstance(ut, UUIDType)

    def test_from_str(self):
        """Create from string."""
        ut = UUIDType.from_str("12345678-1234-5678-1234-567812345678")
        assert isinstance(ut, UUIDType)

    def test_from_str_no_hyphens(self):
        """Create from string without hyphens."""
        ut = UUIDType.from_str("12345678123456781234567812345678")
        assert isinstance(ut, UUIDType)

    def test_from_bytes(self):
        """Create from 16 bytes."""
        ut = UUIDType.from_bytes(b"\x12\x34\x56\x78" * 4)
        assert isinstance(ut, UUIDType)

    def test_from_int(self):
        """Create from 128-bit integer."""
        ut = UUIDType.from_int(0x12345678123456781234567812345678)
        assert isinstance(ut, UUIDType)


# =============================================================================
# UUIDTYPE COMPONENT ACCESSOR TESTS
# =============================================================================


class TestUUIDTypeAccessors:
    """UUIDType component accessor tests."""

    def test_version_returns_inttype(self):
        """version() returns IntType."""
        ut = UUIDType.uuid4()
        result = ut.version()
        assert isinstance(result, IntType)

    def test_variant_returns_strtype(self):
        """variant() returns StrType."""
        ut = UUIDType.uuid4()
        result = ut.variant()
        assert isinstance(result, StrType)

    def test_time_returns_inttype(self):
        """time() returns IntType."""
        ut = UUIDType.uuid1()
        result = ut.time()
        assert isinstance(result, IntType)

    def test_clock_seq_returns_inttype(self):
        """clock_seq() returns IntType."""
        ut = UUIDType.uuid1()
        result = ut.clock_seq()
        assert isinstance(result, IntType)

    def test_node_returns_inttype(self):
        """node() returns IntType."""
        ut = UUIDType.uuid1()
        result = ut.node()
        assert isinstance(result, IntType)


# =============================================================================
# UUIDTYPE CONVERSION TESTS
# =============================================================================


class TestUUIDTypeConversions:
    """UUIDType conversion tests."""

    def test_hex_returns_strtype(self):
        """hex() returns StrType."""
        ut = UUIDType.uuid4()
        result = ut.hex()
        assert isinstance(result, StrType)

    def test_urn_returns_strtype(self):
        """urn() returns StrType."""
        ut = UUIDType.uuid4()
        result = ut.urn()
        assert isinstance(result, StrType)

    def test_bytes_returns_bytestype(self):
        """bytes() returns BytesType."""
        ut = UUIDType.uuid4()
        result = ut.bytes()
        assert isinstance(result, BytesType)

    def test_bytes_le_returns_bytestype(self):
        """bytes_le() returns BytesType."""
        ut = UUIDType.uuid4()
        result = ut.bytes_le()
        assert isinstance(result, BytesType)

    def test_int_returns_inttype(self):
        """int_() returns IntType."""
        ut = UUIDType.uuid4()
        result = ut.int_()
        assert isinstance(result, IntType)
