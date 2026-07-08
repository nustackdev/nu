"""Persistent-counter bracket-tree Nu app: rocksdb-navigator preset.

Same shape as ``basic.py`` but the preset swaps the mem stack for a full
RocksDB stack -- Codec + InMemoryObserver + RocksDBStorage + Navigator, all
composed as one bracket. Counter survives across runs; if you re-run this
script you'll see the value climb.

Run: python examples/brackets/rocksdb.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import nu
from nu.domains.shape import Shape
from nu.virtuals import IntRef


class Counter(Shape):
    """One int slot, backed by RocksDB."""

    value = IntRef.slot()


# Init-if-missing -> bump -> read.
body = (
    nu.v.Transaction(
        nu.IfDo(Counter.value.missing(), Counter.value.store(0))
        >> Counter.value.store(Counter.value + 1),
    )
    >> nu.v.Snapshot(nu.print(Counter.value))
)


if __name__ == "__main__":
    # Ephemeral dir for the example. Point at a real path to persist across runs.
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "counter.db")
        tree = nu.With(
            nu.v.presets.rocksdb_navigator_inmemory(db_path),
            body=body,
        )
        # First run: fresh db, counter -> 1.
        nu.run(tree)
        # Second run over the same tree: counter -> 2 (persistence).
        nu.run(tree)
