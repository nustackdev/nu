"""Value term implementations.

ValueTerms represent pure computed values (R-values):
- PathValue: Reading a path (bridge from PathTerm to ValueTerm)
- LiteralValue: Constants (42, "hello", True)
- BinaryOp: Binary operations (>, <, ==, +, -, *, /, &, |)
- UnaryOp: Unary operations (not, -, +)
- DomainTypeExpr: Links expression class to implementation class
- MethodCallValue: Calls methods on domain types
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from redwood.dsl.term import PathTerm, ValueTerm
from redwood.dsl.types import NaN, is_special, propagate_special


if TYPE_CHECKING:
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree


class PathValue(ValueTerm):
    """Path value: reading a path location.

    This is the bridge from PathTerm (L-value) to ValueTerm (R-value).
    Created by PathTerm.get() or implicitly in value contexts.

    Example:
        value = User.age.get()  # Explicit PathValue
        # OR
        value = User.age > 18  # Implicit PathValue inside comparison
    """

    def __init__(self, path: PathTerm) -> None:
        """Initialize path value.

        Args:
            path: PathTerm to read
        """
        super().__init__()
        self.path = path

        # Inherit metadata from path
        self.meta.value_type = path.meta.primitive_type
        if path.meta.resolved_path:
            self.meta.dependencies = frozenset([str(path.meta.resolved_path)])
        else:
            self.meta.dependencies = frozenset()

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> object:
        """Evaluate by reading path value.

        Delegates to path's .get() operation.

        Args:
            tree: Tree instance
            ctx: Context for data access

        Returns:
            Value at path, or Empty if doesn't exist
        """
        # Use the existing GetOperation infrastructure
        from redwood.dsl.operations import GetOperation
        from redwood.tree.view import DictView

        # Get parent view type (default to DictView)
        if hasattr(self.path, "_parent_view_type"):
            view_type = self.path._parent_view_type  # type: ignore[attr-defined]
        else:
            view_type = DictView

        get_op = GetOperation(self.path, view_type)
        return get_op.evaluate(tree, ctx)


class LiteralValue(ValueTerm):
    """Literal constant value: 42, "hello", True, 3.14.

    Represents a constant value in an expression.
    Always pure, always constant.

    Example:
        ten = LiteralValue(10)
        hello = LiteralValue("hello")
    """

    def __init__(self, value: object) -> None:
        """Initialize literal value.

        Args:
            value: The literal constant
        """
        super().__init__()
        self.value = value

        # Metadata
        self.meta.value_type = type(value)
        self.meta.is_constant = True

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> object:
        """Evaluate to literal value.

        Args:
            tree: Tree instance (unused)
            ctx: Context (unused)

        Returns:
            The literal value
        """
        return self.value


# Operation implementations with Empty/NaN propagation
_OPERATORS = {
    # Comparison
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "ge": lambda a, b: a >= b,
    "le": lambda a, b: a <= b,
    # Arithmetic
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: NaN if b == 0 else a / b,
    "mod": lambda a, b: NaN if b == 0 else a % b,
    "pow": lambda a, b: a**b,
    # Logical
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
}


class BinaryOp(ValueTerm):
    """Binary operation: a > b, a + b, a & b.

    Represents any binary operation between two value terms.
    Handles Empty/NaN propagation automatically.

    Supported operations:
    - Comparison: gt, lt, eq, ne, ge, le
    - Arithmetic: add, sub, mul, div, mod, pow
    - Logical: and, or

    Example:
        op = BinaryOp("gt", PathValue(User.age), LiteralValue(18))
        result = op.evaluate(tree, ctx)  # Returns bool
    """

    def __init__(self, op: str, left: ValueTerm, right: ValueTerm) -> None:
        """Initialize binary operation.

        Args:
            op: Operation name (gt, lt, eq, add, sub, mul, div, and, or)
            left: Left operand
            right: Right operand
        """
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

        # Determine result type
        if op in ("gt", "lt", "eq", "ne", "ge", "le", "and", "or"):
            self.meta.value_type = bool
        elif op in ("add", "sub", "mul", "div", "mod", "pow"):
            # Inherit from operands (simplified)
            self.meta.value_type = left.meta.value_type or right.meta.value_type

        # Pure if both operands are pure
        self.meta.is_pure = left.meta.is_pure and right.meta.is_pure

        # Merge dependencies
        self.meta.dependencies = left.meta.dependencies | right.meta.dependencies

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> object:
        """Evaluate binary operation with Empty/NaN propagation.

        Args:
            tree: Tree instance
            ctx: Context

        Returns:
            Operation result, or NaN if operands are special values
        """
        # Evaluate operands
        left_val = self.left.evaluate(tree, ctx)
        right_val = self.right.evaluate(tree, ctx)

        # Propagate special values
        special = propagate_special(left_val, right_val)
        if special is not None:
            return special

        # Apply operation
        operator = _OPERATORS.get(self.op)
        if operator is None:
            raise ValueError(f"Unknown operator: {self.op}")

        try:
            return operator(left_val, right_val)
        except (TypeError, ValueError, ZeroDivisionError):
            # Type mismatches or invalid operations → NaN
            return NaN


_UNARY_OPERATORS = {
    "not": lambda a: not a,
    "neg": lambda a: -a,
    "pos": lambda a: +a,
}


class UnaryOp(ValueTerm):
    """Unary operation: not a, -a, +a.

    Represents any unary operation on a value term.
    Handles Empty/NaN propagation automatically.

    Supported operations:
    - not: logical negation
    - neg: arithmetic negation (-)
    - pos: arithmetic positive (+)

    Example:
        op = UnaryOp("not", PathValue(User.active))
        result = op.evaluate(tree, ctx)  # Returns bool
    """

    def __init__(self, op: str, operand: ValueTerm) -> None:
        """Initialize unary operation.

        Args:
            op: Operation name (not, neg, pos)
            operand: Operand term
        """
        super().__init__()
        self.op = op
        self.operand = operand

        # Determine result type
        if op == "not":
            self.meta.value_type = bool
        else:
            self.meta.value_type = operand.meta.value_type

        # Inherit purity
        self.meta.is_pure = operand.meta.is_pure
        self.meta.dependencies = operand.meta.dependencies

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> object:
        """Evaluate unary operation with Empty/NaN propagation.

        Args:
            tree: Tree instance
            ctx: Context

        Returns:
            Operation result, or NaN if operand is special value
        """
        # Evaluate operand
        operand_val = self.operand.evaluate(tree, ctx)

        # Propagate special values
        special = propagate_special(operand_val)
        if special is not None:
            return NaN

        # Apply operation
        operator = _UNARY_OPERATORS.get(self.op)
        if operator is None:
            raise ValueError(f"Unknown unary operator: {self.op}")

        try:
            return operator(operand_val)
        except (TypeError, ValueError):
            return NaN


class DomainTypeExpr(ValueTerm):
    """Links expression class to implementation class.

    This is the core of the two-class pattern for domain types.
    Created when a domain type is instantiated during expression building.

    The two-class pattern:
    - Expression class (e.g., EMAExpr) - for building expressions (lazy)
    - Implementation class (e.g., EMA) - for execution (evaluates)

    Example:
        # Expression building (lazy)
        ema_expr = EMAExpr(Market.price, window=20)
        # ↓ Creates DomainTypeExpr internally

        # Evaluation (executes)
        ema_expr.evaluate(tree, ctx)
        # ↓ Reads Market.price value
        # ↓ Constructs EMA(value, window=20)
        # ↓ Returns EMA instance
    """

    def __init__(
        self,
        expr_class: type,
        impl_class: type,
        inner: ValueTerm,
        init_kwargs: dict[str, Any],
    ) -> None:
        """Initialize domain type expression.

        Args:
            expr_class: Expression class (e.g., EMAExpr)
            impl_class: Implementation class (e.g., EMA)
            inner: Source value term (e.g., PathValue(Market.price))
            init_kwargs: Constructor arguments for impl_class
        """
        super().__init__()
        self.expr_class = expr_class
        self.impl_class = impl_class
        self.inner = inner
        self.init_kwargs = init_kwargs

        # Inherit metadata from inner
        self.meta.is_pure = inner.meta.is_pure
        self.meta.dependencies = inner.meta.dependencies

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> object:
        """Evaluate inner expression and construct implementation instance.

        Flow:
        1. Evaluate inner expression to get raw value
        2. Construct implementation instance with value + kwargs
        3. Return implementation instance

        Args:
            tree: Tree instance
            ctx: Context

        Returns:
            Implementation instance (e.g., EMA object)
        """
        # Evaluate the source expression to get raw value
        raw_value = self.inner.evaluate(tree, ctx)

        # Handle special values
        if is_special(raw_value):
            raise ValueError(f"{self.impl_class.__name__} received special value: {raw_value}")

        # Construct implementation instance with the value
        impl_instance = self.impl_class(raw_value, **self.init_kwargs)

        return impl_instance


class MethodCallValue(ValueTerm):
    """Method call on a domain type.

    Represents calling a method on a domain type implementation.
    Stores the callable reference (not a string!) for execution.

    Example:
        # Building (lazy)
        is_trending = ema_expr.is_trending_up()
        # ↓ Creates MethodCallValue(domain_expr, "is_trending_up", EMA.is_trending_up)

        # Evaluation (executes)
        result = is_trending.evaluate(tree, ctx)
        # ↓ Evaluates domain_expr → EMA instance
        # ↓ Calls EMA.is_trending_up() on instance
        # ↓ Returns bool
    """

    def __init__(
        self,
        domain_expr: DomainTypeExpr,
        method_name: str,
        method: Callable,
        arg_exprs: dict[str, ValueTerm] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Initialize method call.

        Args:
            domain_expr: Domain type expression
            method_name: Method name (for debugging)
            method: Actual method to call (callable reference)
            arg_exprs: Expression arguments (evaluated at runtime)
            kwargs: Literal keyword arguments
        """
        super().__init__()
        self.domain_expr = domain_expr
        self.method_name = method_name
        self.method = method
        self.arg_exprs = arg_exprs or {}
        self.kwargs = kwargs or {}

        # Inherit metadata
        self.meta.is_pure = domain_expr.meta.is_pure
        self.meta.dependencies = domain_expr.meta.dependencies

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> object:
        """Evaluate domain expression and call method on result.

        Flow:
        1. Evaluate domain expression → implementation instance
        2. Evaluate any expression arguments
        3. Call method on implementation instance
        4. Return result

        Args:
            tree: Tree instance
            ctx: Context

        Returns:
            Method result
        """
        # 1. Evaluate domain expression to get implementation instance
        impl_instance = self.domain_expr.evaluate(tree, ctx)

        # 2. Evaluate any expression arguments
        eval_kwargs = dict(self.kwargs)  # Start with literal kwargs
        for name, arg_expr in self.arg_exprs.items():
            eval_kwargs[name] = arg_expr.evaluate(tree, ctx)

        # 3. Call method on implementation instance
        result = self.method(impl_instance, **eval_kwargs)

        return result
