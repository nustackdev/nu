"""Reference implementations - addressable locations in tree.

Refs are LValues that point to specific locations in the tree.

Ref Types:
    - ValueRef: Points to primitive nodes in the tree (int, float, str, bool, dict, etc..)
    - MapRef: Points to mapping containers (key → value)
    - MapItemRef: Points to specific item in mapping

Key Properties:
    - Path caching: static_path computed at construction (O(1) resolution)
    - Dynamic support: is_dynamic flag + key_expr for runtime evaluation
    - Protocol-aware: view_type links to concrete view class

Resolution Strategy:
    Static refs:  return cached static_path (O(1))
    Dynamic refs: walk parent chain, evaluate expressions (O(depth))

Navigation Patterns:
    ValueRef:        Market.signal
    MapRef:          Market.orders
    MapItemRef:      Market.orders["AAPL"]  (static key)
    MapItemRef:      Market.orders[expr]    (dynamic key)

Example:
    # Static navigation
    ref = ValueRef("price", float, DictView, parent=None)
    ref.static_path  # → ("price",)
    ref.resolve(ctx)  # → ("price",) [cached]

    # Dynamic navigation
    ticker_expr = signal_ref.get()  # RValue expression
    item_ref = orders_ref[ticker_expr]  # MapItemRef
    item_ref.is_dynamic  # → True
    item_ref.resolve(ctx)  # → evaluates ticker_expr → ("orders", "AAPL")
"""
