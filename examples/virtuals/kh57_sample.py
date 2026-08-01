"""kh57 fabric: sparse int-keyed map with range reservoir sampling.

The Kh57Ref sits on top of a virtuals Kh57View: items are stored under
kh57-encoded child segments so range reservoir sampling (kh57.sample) runs
with low read amplification. Semantically it is a sparse ``Mapping[int, V]``:
put, get, iterate in original int order, plus ``.sample(n, begin, end)`` and
``.range(begin, end)``.

Below: a Ledger shape with a Kh57Ref-backed ``entries`` slot. Load 100k
entries, then sample 500 uniformly from a sub-range and take an ordered
range slice - deterministic given the seeded rng, stable under out-of-range
appends.
"""

from __future__ import annotations

import random

from nu import Context, run
from nu.domains.shape import Shape
from nu.virtuals import IntRef, Kh57Ref
from nu.virtuals.interactions.kh57 import Kh57SampleQuery
from nu.virtuals.presets import memory_storage
from virtuals import Navigator
from virtuals.tkv.storage import TransactionProtocol


# ============================================================================
# Shape
# ============================================================================


class Ledger(Shape):
    """Ledger of int-keyed entries with efficient range sampling."""

    height = IntRef.slot()
    entries = Kh57Ref.slot(int)


# ============================================================================
# Run
# ============================================================================


def main() -> None:
    """Load a Ledger, then sample and range-slice its entries."""
    with memory_storage() as storage:
        with storage.transaction() as tx:
            ctx = Context().bind(Navigator, Navigator(storage)).bind(TransactionProtocol, tx)

            # Load 100_000 entries.
            print("loading 100k entries...")
            for k in range(100_000):
                run(Ledger.entries.set_item(k, k * 2), ctx)

            print(f"len = {run(Ledger.entries.len(), ctx)[0]}")

            # Sample 500 uniformly from [10_000, 20_000).
            sample_q = Kh57SampleQuery(
                Ledger.entries,
                500,
                10_000,
                20_000,
                rng=random.Random(0),  # noqa: S311
            )
            samples = run(sample_q, ctx)[0]
            print(f"\nsample 500 from [10_000, 20_000): got {len(samples)} items")
            first_five_keys = sorted(k for k, _ in samples)[:5]
            print(f"  first five sampled keys (sorted): {first_five_keys}")
            assert all(10_000 <= k < 20_000 for k, _ in samples)

            # Ordered range slice [42_000, 42_010).
            slice_result = run(Ledger.entries.range(42_000, 42_010), ctx)[0]
            print(f"\nrange [42_000, 42_010): {slice_result}")


if __name__ == "__main__":
    main()
