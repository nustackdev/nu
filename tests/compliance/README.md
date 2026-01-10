# Storage Protocol Compliance Tests

This directory contains abstract test suites for verifying storage adapter compliance with the `StorageProtocol` interface.

## Purpose

These are "smoke tests" - basic checks that verify protocol compliance without exercising advanced features like:

- Parallelism and concurrent transactions
- Isolation level guarantees
- Performance characteristics
- Large-scale operations

The goal is to provide a thin, reusable test framework that catches basic protocol violations and ensures minimal compliance.

## Usage

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

## Test Coverage

The compliance suite tests:

### Transaction Creation (6 tests)

- `test_begin_transaction` - Read-write transactions
- `test_begin_snapshot` - Read-only snapshots
- `test_begin_write_batch` - Write-only batches
- `test_begin_with_read_only` - begin(read_only=True)
- `test_begin_with_write_only` - begin(write_only=True)
- `test_begin_with_no_flags` - begin() default behavior

### Context Managers (6 tests)

- `test_transaction_context_manager_commit` - Auto-commit on success
- `test_transaction_context_manager_abort` - Auto-abort on exception
- `test_snapshot_context_manager` - Auto-close snapshots
- `test_batch_write_context_manager_commit` - Batch commit
- `test_batch_write_context_manager_abort` - Batch abort on exception

### Basic CRUD (6 tests)

- `test_put_get` - Basic put/get operations
- `test_put_update_get` - Update existing keys
- `test_delete` - Delete existing keys
- `test_delete_nonexistent` - Delete missing keys
- `test_has` - Key existence checks
- `test_get_missing_key` - Error on missing keys

### Multiget (3 tests)

- `test_multiget` - Retrieve multiple keys
- `test_multiget_partial` - Handle missing keys
- `test_multiget_empty` - Empty key lists

### Transaction Lifecycle (4 tests)

- `test_commit` - Explicit transaction commit
- `test_abort` - Explicit transaction abort
- `test_write_batch_write` - Explicit batch write
- `test_write_batch_abort` - Explicit batch abort

### Error Cases (5 tests)

- `test_closed_transaction_read` - Error on closed reads
- `test_closed_transaction_write` - Error on closed writes
- `test_snapshot_write_forbidden` - Snapshots are read-only
- `test_write_batch_read_forbidden` - Batches are write-only
- `test_double_commit` - Error on double commit
- `test_commit_after_abort` - Error on commit after abort

## Extending the Suite

You can add custom tests to your implementation-specific test class:

```python
class TestMyStorageAdapter(StorageProtocolCompliance):
    @pytest.fixture
    def storage(self):
        return MyStorage("/tmp/test.db")

    def test_my_custom_feature(self, storage):
        """Test implementation-specific feature."""
        # Your custom tests here
        pass
```
