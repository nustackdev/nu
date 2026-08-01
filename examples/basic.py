"""Basic Nu bracket-tree app: mem preset + tiny compute."""

from __future__ import annotations

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


tree = nu.With(
    nu.v.presets.memory_navigator(),
    body=nu.v.Transaction(Counter.value.set(0) >> Counter.value.set(Counter.value + 42))
    >> nu.v.Snapshot(nu.print(Counter.value)),
)


if __name__ == "__main__":
    nu.run(tree)
