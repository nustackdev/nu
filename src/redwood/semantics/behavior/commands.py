"""Impure commands - mutations with side effects.

Commands are RValues that modify state. They:
    - Have side effects (is_pure = False)
    - Cannot be cached (different result each time tree changes)
    - Should be executed carefully (order matters)
    - Delegate to mutable view protocols

Command Types:
    - SetCmd: Write value to ref location
    - DeleteCmd: Remove value at ref location

Execution Flow (SetCmd):
    1. resolve_ref(ref, ctx) → path segments
    2. navigate_to_parent(tree, parent_path, ctx) → tree node
    3. get_view(node, view_type, ctx) → mutable view instance
    4. view.set(key, value) → writes to tree

Transaction Requirements:
    Commands MUST be executed within a transaction context:

    ✓ Correct:
        with tree.transaction() as storage_ctx:
            ctx = Context(tree, storage_ctx)
            cmd.execute(ctx)

    ✗ Wrong:
        with tree.snapshot() as storage_ctx:  # Read-only!
            ctx = Context(tree, storage_ctx)
            cmd.execute(ctx)  # → Will fail

Design Philosophy:
    - Explicit impurity (is_pure = False clearly marked)
    - Transactional safety (rely on tree transactions)
    - Fail fast (errors propagate, no silent failures)
    - Protocol delegation (commands don't know storage)

Usage Patterns:
    # Single write
    Market.signal.set(42.0).execute(ctx)

    # Conditional write
    if price.get().execute(ctx) > 100:
        Market.orders["AAPL"].remove().execute(ctx)

    # Batch writes (in transaction)
    with tree.transaction() as storage_ctx:
        ctx = Context(tree, storage_ctx)
        Market.signal.set(99.0).execute(ctx)
        Market.orders["AAPL"].price.set(150.0).execute(ctx)
        # Atomically committed

Why Commands Return None:
    - Side effects are the point (not return values)
    - Prevents confusion (don't use result in expressions)
    - Explicit separation (operations produce, commands mutate)
"""
