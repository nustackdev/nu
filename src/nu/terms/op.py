"""Op - operation hierarchy.

Operations transform inputs to outputs:

    Nu                          - the primitive
    └── RValue                  - evaluable expression
        └── Op                  - operation (maps inputs to outputs)
            └── NAryOp          - op with operands and sentinel handling
                ├── UnaryOp     - single operand
                ├── BinaryOp    - two operands
                └── TernaryOp   - three operands

Three orthogonal dimensions:

    Purity (how it behaves):
        - Calculation (Calc): pure (no side effects)
        - Command (Cmd): impure (has side effects)

    Arity (how many operands):
        - NAryOp, UnaryOp, BinaryOp, TernaryOp
        - execute = resolve children -> propagate sentinels -> apply()

    Lifecycle (resource scoping):
        - ScopedOp: before/after/after_failure hooks
        - execute = before(ctx) -> run children sequentially -> after/after_failure

Convenience classes (purity x arity):
    - NAryCalc / NAryCmd
    - UnaryCalc / UnaryCmd
    - BinaryCalc / BinaryCmd
    - TernaryCalc / TernaryCmd

Convenience classes (purity x lifecycle):
    - ScopedCalc / ScopedCmd

Composition pattern:
    class AddCalc(BinaryCalc[float]):
        def apply(self, left: float, right: float) -> float:
            return left + right
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .nu import Nu, RValue
from .sentinel import INVALID, Sentinel, is_sentinel
from .type_vars import T_co


if TYPE_CHECKING:
    from ..context import Context


__all__ = [  # noqa: RUF022
    # Base
    "Op",
    "NAryOp",
    "UnaryOp",
    "BinaryOp",
    "TernaryOp",
    # Purity
    "Calculation",
    "Command",
    # Lifecycle
    "ScopedOp",
    # Purity + arity
    "NAryCalc",
    "NAryCmd",
    "UnaryCalc",
    "UnaryCmd",
    "BinaryCalc",
    "BinaryCmd",
    "TernaryCalc",
    "TernaryCmd",
    # Purity + lifecycle
    "ScopedCalc",
    "ScopedCmd",
]


# =============================================================================
# OP BASE
# =============================================================================


class Op(RValue[T_co], ABC):
    """Operation. Maps inputs to outputs.

    Ops are the fundamental unit of computation:
    - UnaryOp: single operand (-x, abs(x), not x)
    - BinaryOp: two operands (x + y, x > y)
    - TernaryOp: three operands (if a then b else c)

    Extend NAryOp for operand-based ops with sentinel propagation.
    Extend ScopedOp for resource lifecycle (before/after hooks).
    Extend Op directly for custom execution.
    """

    def __init__(self, *children: object) -> None:
        """Initialize with operands. Python literals are wrapped into Values."""
        # FIXME: This is a core circular dependency!!
        from nu.utils import ensure_nu

        super().__init__(*[ensure_nu(c) for c in children])


# =============================================================================
# N-ARY OP WITH OPERAND MANAGEMENT
# =============================================================================


class NAryOp(Op[T_co | Sentinel], ABC):
    """Op with operands. Handles resolution and sentinels.

    Subclasses with fixed arity should use UnaryOp, BinaryOp, or
    TernaryOp. Subclasses with variable arity can override __init__.

    Sentinel propagation:
        If any operand resolves to a sentinel (EMPTY, INVALID),
        the op returns INVALID without calling apply().
    """

    def __init__(self, *children: object) -> None:
        """Initialize with operands."""
        super().__init__(*children)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        args = ", ".join(str(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    # =========================================================================
    # EXECUTION
    # =========================================================================

    async def execute(self, ctx: Context) -> T_co | Sentinel:
        """Resolve operands, propagate sentinels, apply transformation."""
        values = []
        for child in self.children:
            val = await child.execute(ctx)
            if is_sentinel(val):
                return INVALID
            values.append(val)
        return self.apply(*values)

    @abstractmethod
    def apply(self, *values: Any) -> T_co | Sentinel:  # noqa: ANN401
        """Apply the transformation to resolved values.

        Called after all operands are resolved and verified non-sentinel.

        Args:
            *values: Resolved operand values (never sentinels)

        Returns:
            Result of the transformation
        """
        ...


# =============================================================================
# ARITY-SPECIFIC OPS
# =============================================================================


class UnaryOp(NAryOp[T_co], ABC):
    """Single operand op. For: -x, abs(x), not x, len(x), etc."""

    def __init__(self, operand: object) -> None:
        super().__init__(operand)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.operand!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.operand})"

    @property
    def operand(self) -> Nu:
        """The single operand."""
        return self._children[0]

    @abstractmethod
    def apply(self, operand: Any) -> T_co | Sentinel:  # type: ignore[override]  # noqa: ANN401
        """Apply."""
        ...


class BinaryOp(NAryOp[T_co], ABC):
    """Two operand op. For: x + y, x > y, x and y, x[y], etc."""

    def __init__(self, left: object, right: object) -> None:
        super().__init__(left, right)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.left!r}, {self.right!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.left}, {self.right})"

    @property
    def left(self) -> Nu:
        """Left operand."""
        return self._children[0]

    @property
    def right(self) -> Nu:
        """Right operand."""
        return self._children[1]

    @abstractmethod
    def apply(self, left: Any, right: Any) -> T_co | Sentinel:  # type: ignore[override]  # noqa: ANN401
        """Apply."""
        ...


class TernaryOp(NAryOp[T_co], ABC):
    """Three operand op. For: if a then b else c, slice(a, b, c), etc."""

    def __init__(self, first: object, second: object, third: object) -> None:
        super().__init__(first, second, third)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.first!r}, {self.second!r}, {self.third!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.first}, {self.second}, {self.third})"

    @property
    def first(self) -> Nu:
        """First operand."""
        return self._children[0]

    @property
    def second(self) -> Nu:
        """Second operand."""
        return self._children[1]

    @property
    def third(self) -> Nu:
        """Third operand."""
        return self._children[2]

    @abstractmethod
    def apply(self, first: Any, second: Any, third: Any) -> T_co | Sentinel:  # type: ignore[override]  # noqa: ANN401
        """Apply."""
        ...


# =============================================================================
# PURITY MIXINS
# =============================================================================


class Calculation(Op[T_co], ABC):
    """Pure Op. No side effects.

    Calculations are:
    - Deterministic: same inputs -> same output
    - Side-effect free: don't modify state
    - Cacheable: results can be memoized
    - Reorderable: execution order doesn't matter

    Inherit directly for complex ops that override execute().
    Combine with arity mixins (UnaryCalc, BinaryCalc) for
    simple ops that use the apply() pattern.

    Usage::

        # Simple: arity mixin provides execute -> apply
        class AddCalc(BinaryCalc[float]):
            def apply(self, left: float, right: float) -> float:
                return left + right

        # Complex: override execute directly
        class Filter(Calculation):
            def __init__(self, items, *, condition, body, item="item"):
                super().__init__(items, condition, body, item)
            async def execute(self, ctx):
                ...
    """

    @property
    def is_self_pure(self) -> bool:
        """Calculations are pure by definition."""
        return True


class Command(Op[T_co], ABC):
    """Impure Op. Has side effects.

    Commands modify state and must be executed carefully:
    - Order-dependent: sequence of execution matters
    - Transactional: should run within a ScopedCmd
    - Not cacheable: results may differ each execution

    Inherit directly for complex impure ops that override execute().
    Combine with arity mixins (UnaryCmd, BinaryCmd) for simple ops
    that use the apply() pattern.

    Usage::

        # Simple: arity mixin provides execute -> apply
        class SetCmd(UnaryCmd[T]):
            def apply(self, value: T) -> T:
                return value

        # Complex: override execute directly
        class Print(Command):
            async def execute(self, ctx):
                print(await self.children[0].execute(ctx))
    """

    @property
    def is_self_pure(self) -> bool:
        """Commands are always impure by definition."""
        return False


# =============================================================================
# LIFECYCLE
# =============================================================================


class ScopedOp(Op[None], ABC):
    """Op with resource lifecycle hooks.

    Scoped ops run children sequentially within a before/after boundary.
    Override hooks to scope context, manage resources, or add instrumentation.

    Hooks:
        before(ctx) -> ctx:          Set up resources, return scoped context.
        after(ctx):                  Clean up after successful execution.
        after_failure(ctx, error):   Clean up after failed execution.

    Default execute runs all children sequentially, returns None.
    Override execute for custom execution logic while still using hooks.

    Usage::

        class Atomic(ScopedCmd):
            def __init__(self, *children, scope=None):
                super().__init__(*children, scope)
            def before(self, ctx):
                return ctx.bind(Transaction, factory=open_tx)
            def after(self, ctx):
                ctx.get(Transaction).commit()
            def after_failure(self, ctx, error):
                ctx.get(Transaction).abort()
    """

    async def execute(self, ctx: Context) -> None:
        """Execute with lifecycle: before -> run children -> after/after_failure."""
        scoped_ctx = self.before(ctx)
        try:
            for child in self.children:
                await child.execute(scoped_ctx)
            self.after(scoped_ctx)
        except BaseException as e:
            self.after_failure(scoped_ctx, e)
            raise

    def before(self, ctx: Context) -> Context:
        """Set up resources, return scoped context for children."""
        return ctx

    def after(self, ctx: Context) -> None:
        """Clean up after successful execution."""

    def after_failure(self, ctx: Context, error: BaseException) -> None:
        """Clean up after failed execution."""


# =============================================================================
# CONVENIENCE: PURITY + ARITY COMBINATIONS
# =============================================================================


class NAryCalc(Calculation, NAryOp[T_co]):
    """Pure NAry op."""

    pass


class NAryCmd(Command, NAryOp[T_co]):
    """Impure NAry op."""

    pass


class UnaryCalc(Calculation, UnaryOp[T_co]):
    """Pure unary op."""

    pass


class UnaryCmd(Command, UnaryOp[T_co]):
    """Impure unary op."""

    pass


class BinaryCalc(Calculation, BinaryOp[T_co]):
    """Pure binary op."""

    pass


class BinaryCmd(Command, BinaryOp[T_co]):
    """Impure binary op."""

    pass


class TernaryCalc(Calculation, TernaryOp[T_co]):
    """Pure ternary op."""

    pass


class TernaryCmd(Command, TernaryOp[T_co]):
    """Impure ternary op."""

    pass


# =============================================================================
# CONVENIENCE: PURITY + LIFECYCLE COMBINATIONS
# =============================================================================


class ScopedCalc(Calculation, ScopedOp):
    """Pure scoped op. Resource lifecycle without side effects."""

    pass


class ScopedCmd(Command, ScopedOp):
    """Impure scoped op. Resource lifecycle with side effects."""

    pass
