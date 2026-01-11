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
    binary_key_filters: tuple of KeyFilter() for not yet decoded keys - super fast
    decoded_key_filters: tuple of KeyFilter() for decoded tuple keys
    binary_value_filters: tuple of ValueFilter() for not yet decoded values (e.g. fitler by size)
    decoded_value_filters: tuple of ValueFilter() for decoded values

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
Filtering mechanism is similar to observer's notification filtering mechanism.
