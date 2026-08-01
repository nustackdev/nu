"""RocksDB navigator preset: persistent counter, rerun to increment."""

from __future__ import annotations

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbtest"),
    body=(
        nu.v.Transaction(
            nu.IfDo(Counter.value.missing(), Counter.value.set(0))
            >> Counter.value.set(Counter.value + 1),
        )
        >> nu.v.Snapshot(nu.print(Counter.value))
    ),
)


if __name__ == "__main__":
    nu.run(tree)
