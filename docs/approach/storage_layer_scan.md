# Storage Layer 1 — Scan Operation

`scan` provides ordered, streaming access to key ranges.

It is a **system-level iteration primitive**, not a collection.

## Availability

`scan` is supported in:

- Snapshot
- Transaction

`scan` is not supported in:

- WriteBatch

## Semantics

- Iteration is backend-driven
- Results are streamed, not materialized
- Order follows the storage engine’s native key order
- No guarantees beyond the active context

## Constraints

- `scan` does not imply isolation beyond the context
- `scan` does not observe uncommitted writes outside the context
- `scan` performs no implicit buffering or retries

## Role

`scan` exists to:

- traverse keyspaces
- power higher-level iteration utilities
- expose backend iteration without abstraction leaks

Any stronger guarantees belong in higher layers.

## Mehcanics

scan(self, options: StorageScanOptions) -> ScanProtocol:

StorageScanOptions:
    start: Starting key (inclusive by default). None means from beginning.
    direction: Direction to scan (forward or reverse).
    filter: filter keys
    break_filter: break the scan loop

ScanProtocol:
    def items(self) -> Generator[tuple[key.Key, Value], None, None]:
        """Iterate over (key, value) tuples.

        Yields:
            Tuples of (key, value) for each item in scan range.

        Raises:
            StorageOperationError: If iteration fails.
        """
        ...

    def keys(self) -> Generator[key.Key, None, None]:
        """Iterate over keys only.

        Yields:
            Keys in scan range.

        Raises:
            StorageOperationError: If iteration fails.
        """
        ...

    def values(self) -> Generator[Value, None, None]:
        """Iterate over values only.

        Yields:
            Values in scan range.

        Raises:
            StorageOperationError: If iteration fails.
        """
        ...

Only keys/values are yielded if all Filters match, otherwise items are skipped.
Filters are hashable
