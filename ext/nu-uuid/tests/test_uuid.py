"""Unit tests for UUID ref.

Tests for:
- UUIDRef (constructors, operations, methods)
"""

from uuid import NAMESPACE_DNS

from nu_uuid import UUIDValue as UUIDRef
from nu import BytesValue as BytesRef
from nu import FuncCallOp
from nu import IntValue as IntRef
from nu import StrValue as StrRef


# =============================================================================
# UUIDREF CONSTRUCTION TESTS
# =============================================================================


class TestUUIDRefConstruction:
    """UUIDRef construction tests."""

    def test_uuid4(self):
        """Create random UUID (version 4)."""
        ut = UUIDRef.uuid4()
        assert isinstance(ut, UUIDRef)
        assert isinstance(ut.source, FuncCallOp)

    def test_uuid1(self):
        """Create UUID from host ID and time (version 1)."""
        ut = UUIDRef.uuid1()
        assert isinstance(ut, UUIDRef)

    def test_uuid1_with_node(self):
        """Create UUID with specific node."""
        ut = UUIDRef.uuid1(node=0x0123456789AB)
        assert isinstance(ut, UUIDRef)

    def test_uuid1_with_node_and_clock_seq(self):
        """Create UUID with node and clock sequence."""
        ut = UUIDRef.uuid1(node=0x0123456789AB, clock_seq=0x1234)
        assert isinstance(ut, UUIDRef)

    def test_uuid3(self):
        """Create UUID based on MD5 hash (version 3)."""
        ut = UUIDRef.uuid3(NAMESPACE_DNS, "example.com")
        assert isinstance(ut, UUIDRef)

    def test_uuid5(self):
        """Create UUID based on SHA-1 hash (version 5)."""
        ut = UUIDRef.uuid5(NAMESPACE_DNS, "example.com")
        assert isinstance(ut, UUIDRef)

    def test_from_str(self):
        """Create from string."""
        ut = UUIDRef.from_str("12345678-1234-5678-1234-567812345678")
        assert isinstance(ut, UUIDRef)

    def test_from_str_no_hyphens(self):
        """Create from string without hyphens."""
        ut = UUIDRef.from_str("12345678123456781234567812345678")
        assert isinstance(ut, UUIDRef)

    def test_from_bytes(self):
        """Create from 16 bytes."""
        ut = UUIDRef.from_bytes(b"\x12\x34\x56\x78" * 4)
        assert isinstance(ut, UUIDRef)

    def test_from_int(self):
        """Create from 128-bit integer."""
        ut = UUIDRef.from_int(0x12345678123456781234567812345678)
        assert isinstance(ut, UUIDRef)


# =============================================================================
# UUIDREF COMPONENT ACCESSOR TESTS
# =============================================================================


class TestUUIDRefAccessors:
    """UUIDRef component accessor tests."""

    def test_version_returns_intref(self):
        """version() returns IntRef."""
        ut = UUIDRef.uuid4()
        result = ut.version()
        assert isinstance(result, IntRef)

    def test_variant_returns_strref(self):
        """variant() returns StrRef."""
        ut = UUIDRef.uuid4()
        result = ut.variant()
        assert isinstance(result, StrRef)

    def test_time_returns_intref(self):
        """time() returns IntRef."""
        ut = UUIDRef.uuid1()
        result = ut.time()
        assert isinstance(result, IntRef)

    def test_clock_seq_returns_intref(self):
        """clock_seq() returns IntRef."""
        ut = UUIDRef.uuid1()
        result = ut.clock_seq()
        assert isinstance(result, IntRef)

    def test_node_returns_intref(self):
        """node() returns IntRef."""
        ut = UUIDRef.uuid1()
        result = ut.node()
        assert isinstance(result, IntRef)


# =============================================================================
# UUIDREF CONVERSION TESTS
# =============================================================================


class TestUUIDRefConversions:
    """UUIDRef conversion tests."""

    def test_hex_returns_strref(self):
        """hex() returns StrRef."""
        ut = UUIDRef.uuid4()
        result = ut.hex()
        assert isinstance(result, StrRef)

    def test_urn_returns_strref(self):
        """urn() returns StrRef."""
        ut = UUIDRef.uuid4()
        result = ut.urn()
        assert isinstance(result, StrRef)

    def test_bytes_returns_bytesref(self):
        """bytes() returns BytesRef."""
        ut = UUIDRef.uuid4()
        result = ut.bytes()
        assert isinstance(result, BytesRef)

    def test_bytes_le_returns_bytesref(self):
        """bytes_le() returns BytesRef."""
        ut = UUIDRef.uuid4()
        result = ut.bytes_le()
        assert isinstance(result, BytesRef)

    def test_int_returns_intref(self):
        """int_() returns IntRef."""
        ut = UUIDRef.uuid4()
        result = ut.int_()
        assert isinstance(result, IntRef)
