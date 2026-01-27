"""Runnable demo of the topology language PoC.

Run: python -m poc.topology.example
"""

from __future__ import annotations

from .context import DictKVSubstrate, KVContext
from .executor import execute
from .lang import Add, Atomic, Get, Lit, Ref, RootGroup, Seq, Set
from .transforms import add_logging


def main() -> None:
    """Run the demo."""
    data = {"users": 10, "score": 42, "multiplier": 3}
    sub = DictKVSubstrate(data)

    print("=== Initial state ===")
    print(f"  {sub.data}")
    print()

    # Build the program — pure topology, no imperative details
    app = RootGroup(
        substrates={KVContext: sub},
        child=Seq(
            # 1. Read score (implicit Atomic → Snapshot)
            Get(Ref("score")),

            # 2. Increment score (implicit Atomic → Transaction)
            Set(Ref("score"), Add(Get(Ref("score")), Lit(8))),

            # 3. Explicit Atomic: read + write users together
            Atomic(
                Get(Ref("users")),
                Set(Ref("users"), Add(Get(Ref("users")), Lit(1))),
            ),

            # 4. Compute score * multiplier and store
            Set(Ref("score"), Add(Get(Ref("score")), Get(Ref("multiplier")))),
        ),
    )

    print("=== Tree (before transforms) ===")
    print(f"  {app!r}")
    print()

    # Apply logging transform
    logged_app = RootGroup(
        substrates={KVContext: sub},
        child=add_logging(app.child),
    )

    # Reset data for logged run
    sub.data = {"users": 10, "score": 42, "multiplier": 3}

    print("=== Executing with logging ===")
    result = execute(logged_app)
    print()

    print("=== Final state ===")
    print(f"  {sub.data}")
    print(f"  Last result: {result}")
    print()

    # Verify
    assert sub.data["score"] == 53  # 42+8=50, then 50+3=53
    assert sub.data["users"] == 11  # 10+1
    print("=== All assertions passed ===")


if __name__ == "__main__":
    main()
