"""Pure operations - reads and computations without side effects.

Operations are RValues that produce values deterministically. They:
    - Have no side effects (is_pure = True)
    - Can be cached safely
    - Can be composed freely
    - Delegate to view protocols

Operation Types:
    - GetOp: Read value from ref location
    - LiteralValue: Constant value (42, "hello", True)
    - BinaryOp: Binary operations (>, <, ==, +, -, *, /, and, or)

Execution Flow (GetOp):
    1. resolve_ref(ref, ctx) → path segments
    2. navigate_to_parent(tree, parent_path, ctx) → tree node
    3. get_view(node, view_type, ctx) → view instance
    4. view.get(key) → value or None → Empty

Special Value Handling:
    - Operations propagate Empty/NaN automatically
    - BinaryOp: if any operand is special → NaN
    - Graceful degradation without exceptions

Design Philosophy:
    - Pure by contract (no hidden mutations)
    - Composable (operations return RValues)
    - Fail gracefully (Empty/NaN, not exceptions)
    - Delegate to protocols (operations don't know storage)

Usage Patterns:
    # Simple read
    value = price_ref.get().execute(ctx)

    # Comparison
    is_expensive = BinaryOp("gt", price.get(), LiteralValue(100))
    result = is_expensive.execute(ctx)  # → True/False/NaN

    # Composition
    condition = BinaryOp("and",
        BinaryOp("gt", price.get(), LiteralValue(100)),
        BinaryOp("lt", volume.get(), LiteralValue(1000))
    )

    # Operator overloading (future)
    price.get() > 100  # → constructs BinaryOp("gt", ...)

Why Operations Return RValues:
    - Enables composition: op1.and(op2)
    - Enables lazy evaluation: build expression, execute later
    - Enables optimization: constant folding, dead code elimination
    - Enables serialization: expressions as data
"""
