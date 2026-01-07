"""Computations module - operations and commands for the term layer.

This module provides all computation operations organized by domain:

Submodules:
- bases: Foundation tier (UnaryOp, BinaryOp, TernaryOp base classes)
- value: Value operations (arithmetic, comparison, logical, conversion)
- types: Type-specific operations (string, bytes, sequence, mapping, set)
- ref: Reference operations (access, mutate, sequence, mapping, set)
- reactive: Reactive operations (OnChangeOp, etc.)
- typed: TypedValue operations (FuncCallOp, MethodCallOp, etc.)

Top-level exports:
- Ref operations (MapOp, FilterOp, etc.) work on LValue references
- Type operations from types/ (sequence, string, etc.) work on RValues
- For sequence value operations, import from comps.types.sequence directly

Note on duplicate names:
- MapOp, FilterOp, ReduceOp at top-level are REF operations (lazy, storage)
- types.sequence has equivalent ops for SEQUENCE VALUES (eager, in-memory)
- Use fully-qualified imports when you need the sequence value versions:
    from everyshape.term.comps.types.sequence import MapOp as SeqMapOp
"""
