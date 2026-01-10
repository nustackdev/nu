"""Compliance test framework for storage protocol implementations.

This package provides abstract test suites that storage adapters can inherit
to verify they correctly implement the required protocols. These are "smoke tests"
designed to catch basic protocol violations and ensure minimal compliance.

Usage:
    ```python
    from tests.compliance import StorageProtocolCompliance


    class TestMyStorage(StorageProtocolCompliance):
        @pytest.fixture
        def storage(self):
            db = MyStorage("/tmp/test.db")
            db.open()
            yield db
            db.close()
    ```

Test Suites:
    - StorageProtocolCompliance: Tests for StorageProtocol implementations
      covering transaction creation, CRUD operations, and context managers.

Design Philosophy:
    - Thin: Minimal test coverage focused on protocol compliance
    - Composable: Easy to inherit and extend with custom tests
    - Backend-agnostic: Works with any StorageProtocol implementation
    - Clear errors: Helpful messages when protocol violations are detected

Future Extensions:
    - Parallelism tests (concurrent transactions)
    - Isolation level tests (snapshot isolation, serializable)
    - Performance benchmarks
    - Stress tests (large values, many keys)
"""

from __future__ import annotations

from .test_storage_protocol import StorageProtocolCompliance


__all__ = [
    "StorageProtocolCompliance",
]
