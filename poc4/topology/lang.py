"""Topology language primitives: Unit, Term, Flow, Group."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .context import Context, ContextMap, KVContext, Snapshot, Transaction


# =============================================================================
# Unit — base for all tree nodes
# =============================================================================


class Unit(ABC):
    """Node in the execution tree."""

    def needs(self) -> set[type[Context]]:
        """Context types I require (own + children)."""
        result: set[type[Context]] = set()
        for child in self.children():
            result |= child.needs()
        return result

    def children(self) -> list[Unit]:
        """My child units."""
        return []

    @abstractmethod
    def run(self, ctx: ContextMap) -> Any:
        """Execute with resolved contexts."""
        ...


# =============================================================================
# Term (0-cell) — Point — computation
# =============================================================================


class Term[T](Unit, ABC):
    """Computation node. Returns a value. Children are Terms only."""

    def children(self) -> list[Term]:  # type: ignore[override]
        """Child terms (operands)."""
        return []

    @abstractmethod
    def run(self, ctx: ContextMap) -> T:
        """Compute and return value."""
        ...

    @property
    def is_pure(self) -> bool:
        """Whether this term is pure (no side effects)."""
        return True


class Lit[T](Term[T]):
    """Literal value."""

    def __init__(self, value: T) -> None:
        self.value = value

    def run(self, ctx: ContextMap) -> T:
        """Return the literal value."""
        return self.value

    def __repr__(self) -> str:
        return f"Lit({self.value!r})"


class Ref(Term[str]):
    """Reference to a KV location. Evaluates to its key."""

    def __init__(self, key: str) -> None:
        self.key = key

    def needs(self) -> set[type[Context]]:
        """Ref itself doesn't need context — Get/Set do."""
        return set()

    def run(self, ctx: ContextMap) -> str:
        """Return the key."""
        return self.key

    def __repr__(self) -> str:
        return f"Ref({self.key!r})"


class Get(Term[Any]):
    """Read a value from KV by ref key."""

    def __init__(self, ref: Ref) -> None:
        self.ref = ref

    def needs(self) -> set[type[Context]]:
        """Needs KV read access."""
        return {KVContext}

    def children(self) -> list[Term]:
        """Ref is a child term."""
        return [self.ref]

    def run(self, ctx: ContextMap) -> Any:
        """Read from KV context.

        Uses ctx[KVContext] — the executor ensures this points
        to the innermost Group's context (B4: innermost wins).
        """
        kv = ctx.get(KVContext)
        if kv is None:
            msg = "No KVContext available"
            raise RuntimeError(msg)
        key = self.ref.run(ctx)
        return kv.get(key)

    def __repr__(self) -> str:
        return f"Get({self.ref!r})"


class Set(Term[None]):
    """Write a value to KV. Impure command."""

    def __init__(self, ref: Ref, value: Term) -> None:
        self.ref = ref
        self.value_term = value

    @property
    def is_pure(self) -> bool:
        """Set is impure."""
        return False

    def needs(self) -> set[type[Context]]:
        """Needs KV write access."""
        return {KVContext} | self.value_term.needs()

    def children(self) -> list[Term]:
        """Ref and value are children."""
        return [self.ref, self.value_term]

    def run(self, ctx: ContextMap) -> None:
        """Write to KV context.

        Uses ctx[KVContext] — must be a Transaction (has .put).
        """
        kv = ctx.get(KVContext)
        if kv is None or not isinstance(kv, Transaction):
            msg = "Set requires a Transaction context"
            raise RuntimeError(msg)
        key = self.ref.run(ctx)
        val = self.value_term.run(ctx)
        kv.put(key, val)

    def __repr__(self) -> str:
        return f"Set({self.ref!r}, {self.value_term!r})"


class Add(Term[Any]):
    """Pure addition morphism."""

    def __init__(self, left: Term, right: Term) -> None:
        self.left = left
        self.right = right

    def needs(self) -> set[type[Context]]:
        """Union of children's needs."""
        return self.left.needs() | self.right.needs()

    def children(self) -> list[Term]:
        """Left and right operands."""
        return [self.left, self.right]

    def run(self, ctx: ContextMap) -> Any:
        """Add left and right values."""
        return self.left.run(ctx) + self.right.run(ctx)

    def __repr__(self) -> str:
        return f"Add({self.left!r}, {self.right!r})"


class Mul(Term[Any]):
    """Pure multiplication morphism."""

    def __init__(self, left: Term, right: Term) -> None:
        self.left = left
        self.right = right

    def needs(self) -> set[type[Context]]:
        """Union of children's needs."""
        return self.left.needs() | self.right.needs()

    def children(self) -> list[Term]:
        """Left and right operands."""
        return [self.left, self.right]

    def run(self, ctx: ContextMap) -> Any:
        """Multiply left and right values."""
        return self.left.run(ctx) * self.right.run(ctx)

    def __repr__(self) -> str:
        return f"Mul({self.left!r}, {self.right!r})"


# =============================================================================
# Flow (1-cell) — Path — ordering
# =============================================================================


class Flow(Unit, ABC):
    """Ordering node. Controls execution order of children."""

    @abstractmethod
    def run(self, ctx: ContextMap) -> Any:
        """Execute orchestration logic."""
        ...


class Seq(Flow):
    """Sequential execution. Returns last value."""

    def __init__(self, *units: Unit) -> None:
        self._children = list(units)

    def children(self) -> list[Unit]:
        """Children in order."""
        return self._children

    def run(self, ctx: ContextMap) -> Any:
        """Execute children sequentially, return last value."""
        result = None
        for child in self._children:
            result = child.run(ctx)
        return result

    def __repr__(self) -> str:
        return f"Seq({', '.join(repr(c) for c in self._children)})"


class Par(Flow):
    """Parallel execution (sequential in this PoC). Returns tuple of values."""

    def __init__(self, *units: Unit) -> None:
        self._children = list(units)

    def children(self) -> list[Unit]:
        """Children."""
        return self._children

    def run(self, ctx: ContextMap) -> tuple[Any, ...]:
        """Execute children (sequentially for PoC), return tuple of values."""
        return tuple(child.run(ctx) for child in self._children)

    def __repr__(self) -> str:
        return f"Par({', '.join(repr(c) for c in self._children)})"


class Cond(Flow):
    """Conditional execution. Predicate must be a Term."""

    def __init__(self, pred: Term, then: Unit, else_: Unit) -> None:
        self.pred = pred
        self.then = then
        self.else_ = else_

    def children(self) -> list[Unit]:
        """Predicate, then branch, else branch."""
        return [self.pred, self.then, self.else_]

    def run(self, ctx: ContextMap) -> Any:
        """Branch on predicate value."""
        if self.pred.run(ctx):
            return self.then.run(ctx)
        return self.else_.run(ctx)

    def __repr__(self) -> str:
        return f"Cond({self.pred!r}, {self.then!r}, {self.else_!r})"


# =============================================================================
# Group (2-cell) — Region — cohesion
# =============================================================================


class Group(Unit, ABC):
    """Cohesion boundary. Children share a declared property. Transparent."""

    @abstractmethod
    def run(self, ctx: ContextMap) -> Any:
        """Execute with shared context."""
        ...


class GroupedContext(Group):
    """Children share one context of a specified type."""

    def __init__(self, ctx_type: type[Context], *units: Unit) -> None:
        self.ctx_type = ctx_type
        self._children = list(units)

    def provides(self) -> set[type[Context]]:
        """Context types this group provides."""
        return {self.ctx_type}

    def children(self) -> list[Unit]:
        """Children."""
        return self._children

    def needs(self) -> set[type[Context]]:
        """Children's needs minus what this group provides."""
        child_needs: set[type[Context]] = set()
        for child in self._children:
            child_needs |= child.needs()
        return child_needs - self.provides()

    def run(self, ctx: ContextMap) -> Any:
        """Run children with shared context — actual context managed by executor."""
        result = None
        for child in self._children:
            result = child.run(ctx)
        return result

    def __repr__(self) -> str:
        children = ", ".join(repr(c) for c in self._children)
        return f"GroupedContext({self.ctx_type.__name__}, {children})"


class Atomic(Group):
    """Smart sugar — infers Snapshot vs Transaction from subtree needs."""

    def __init__(self, *units: Unit) -> None:
        self._children = list(units)
        self._inferred_type: type[Context] | None = None

    def infer_context_type(self) -> type[Context] | None:
        """Analyze subtree to pick cheapest sufficient context.

        - Any writes → Transaction
        - Only reads → Snapshot
        - No KV needs → None (no-op)
        """
        if self._inferred_type is not None:
            return self._inferred_type

        has_writes = self._has_writes(self._children)
        has_kv_needs = bool(self._collect_kv_needs())

        if not has_kv_needs:
            self._inferred_type = None
        elif has_writes:
            self._inferred_type = Transaction
        else:
            self._inferred_type = Snapshot

        return self._inferred_type

    def _has_writes(self, units: list[Unit]) -> bool:
        """Check if any unit in the subtree performs writes."""
        for unit in units:
            if isinstance(unit, Set):
                return True
            if isinstance(unit, Term) and not unit.is_pure:
                return True
            if self._has_writes(unit.children()):
                return True
        return False

    def _collect_kv_needs(self) -> set[type[Context]]:
        """Collect KV-related needs from subtree."""
        result: set[type[Context]] = set()
        for child in self._children:
            for need in child.needs():
                if need is KVContext or issubclass(need, KVContext):
                    result.add(need)
        return result

    def provides(self) -> set[type[Context]]:
        """Context types this atomic group provides."""
        ct = self.infer_context_type()
        if ct is None:
            return set()
        return {ct}

    def children(self) -> list[Unit]:
        """Children."""
        return self._children

    def needs(self) -> set[type[Context]]:
        """Children's needs minus what we provide."""
        child_needs: set[type[Context]] = set()
        for child in self._children:
            child_needs |= child.needs()
        provided = self.provides()
        # KVContext need is satisfied by providing Snapshot or Transaction
        result = set()
        for need in child_needs:
            if need is KVContext and any(
                issubclass(p, KVContext) for p in provided
            ):
                continue
            if need not in provided:
                result.add(need)
        return result

    def run(self, ctx: ContextMap) -> Any:
        """Run children — actual context managed by executor."""
        result = None
        for child in self._children:
            result = child.run(ctx)
        return result

    def __repr__(self) -> str:
        children = ", ".join(repr(c) for c in self._children)
        ct = self.infer_context_type()
        ct_name = ct.__name__ if ct else "None"
        return f"Atomic[{ct_name}]({children})"


class RootGroup(Group):
    """Program-lifetime group. Holds substrate factories."""

    def __init__(
        self,
        substrates: dict[type[Context], Any],
        child: Unit,
    ) -> None:
        self.substrates = substrates
        self.child = child

    def children(self) -> list[Unit]:
        """Single child (typically a Flow)."""
        return [self.child]

    def run(self, ctx: ContextMap) -> Any:
        """Run child — substrate lifecycle managed by executor."""
        return self.child.run(ctx)

    def __repr__(self) -> str:
        subs = ", ".join(t.__name__ for t in self.substrates)
        return f"RootGroup([{subs}], {self.child!r})"
