# Storage Protocol Compliance Tests

This directory contains abstract test suites for verifying storage adapter compliance with the `StorageProtocol` interface.

## Purpose

These are "smoke tests" - basic checks that verify protocol compliance.
The goal is to provide a thin, reusable test framework that catches basic protocol violations and ensures minimal compliance.

## Usage Example

To test your storage implementation, inherit from `StorageProtocolCompliance` and override the `storage` fixture:

```python
from tests.compliance import StorageProtocolCompliance

class TestMyStorageAdapter(StorageProtocolCompliance):
    @pytest.fixture
    def storage(self):
        """Provide your storage implementation."""
        db = MyStorage("/tmp/test.db")
        db.open()
        yield db
        db.close()
```

Run the tests:

```bash
pytest tests/integration/test_my_storage.py
```

All compliance tests will automatically run against your storage implementation.
