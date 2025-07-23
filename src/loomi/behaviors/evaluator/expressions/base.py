"""
Unified Base Expression Class

This module provides the foundational Expression class that all Loomi expressions
inherit from. It provides a unified interface for value resolution, contextual
storage access, logging, error handling, and state management.

The design follows a clear separation of concerns:
- Base class handles all infrastructure (logging, errors, utilities)
- Subclasses implement only business logic via do_evaluate()
- Users manage storage contexts (transactions/snapshots) via context managers

Key Features:
- @final evaluate() method provides orchestration
- Unified value resolution (direct values or state paths)
- Storage context abstraction (transactions and snapshots)
- Comprehensive logging with performance tracking
- Configurable error handling and recovery
- Type-safe parameter validation with TypeGuard
- Seamless integration with Loomi state system

Example Usage:
    ```python
    class Calculate(Expression):
        def __init__(self, formula: Union[str, float], target: str, **kwargs):
            super().__init__(**kwargs)
            self.formula = formula
            self.target = target

        def do_evaluate(self, evaluator: Evaluator, context: Context) -> None:
            # User manages storage context via context managers
            with evaluator.state.at("workspace").with_dict_view() as view:
                # Resolve value using view's storage context
                result = self._resolve_value(self.formula, evaluator.state, view.ctx)

                # Store result using same storage context
                target_path = self._parse_state_path(self.target)
                target_view = evaluator.state.at(*target_path).dict_view(ctx=view.ctx)
                target_view.store(result)
    ```
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, TypeGuard, Union, cast, final

if TYPE_CHECKING:
    from loomi.behaviors.evaluator import Context, ErrorBehavior, Evaluator

from loomi.behaviors.state.protocols.kv import SnapshotProtocol
from loomi.behaviors.state.protocols.tree import EmptyProtocol, StateProtocol
from loomi.behaviors.state.protocols.type_vars import TreeValueT

from .logger import logger

# Type definitions
StatePathType = Union[str, Tuple[str, ...]]
ValueOrPath = Union[TreeValueT, str, EmptyProtocol]
StorageContext = Union["SnapshotProtocol", "SnapshotProtocol"]


class ExpressionError(Exception):
    """Base exception for expression-related errors."""

    def __init__(
        self,
        message: str,
        *,
        expression: Optional["Expression"] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.expression = expression
        self.cause = cause


class ValueResolutionError(ExpressionError):
    """Raised when value resolution fails."""

    pass


class Expression(ABC):
    """
    Unified base class for all Loomi expressions.

    Provides a comprehensive foundation for building production-ready expressions
    with minimal implementation effort. The base class handles all infrastructure
    concerns, allowing subclasses to focus purely on business logic.

    Architecture:
    - @final evaluate() handles orchestration (logging, errors, timing)
    - @abstractmethod do_evaluate() is where subclasses implement logic
    - Rich utility methods for value resolution and state access
    - Automatic performance tracking and debugging support
    - User-managed storage contexts via context managers

    Args:
        error_behavior: How to handle errors ("fail" or "continue")
        on_fail: Optional expression to execute when errors occur

    Example:
        ```python
        class SetValue(Expression):
            def __init__(self, path: str, value: Union[str, Any], **kwargs):
                super().__init__(**kwargs)
                self.path = path
                self.value = value

            def do_evaluate(self, evaluator: Evaluator, context: Context) -> None:
                # User manages storage context via context managers
                with evaluator.state.at("temp").with_dict_view() as view:
                    resolved_value = self._resolve_value(self.value, evaluator.state, view.ctx)
                    path_components = self._parse_state_path(self.path)

                    target_view = evaluator.state.at(*path_components).dict_view(ctx=view.ctx)
                    target_view.store(resolved_value)
        ```
    """

    def __init__(
        self,
        *,
        error_behavior: "ErrorBehavior" = "fail",
        on_fail: Optional["Expression"] = None,
        **metadata,
    ):
        """
        Initialize the expression with infrastructure configuration.

        Args:
            error_behavior: How to handle evaluation errors ("fail" or "continue")
            on_fail: Optional fallback expression to execute on error
            **metadata: Additional metadata for debugging and introspection
        """
        # Validate error behavior
        if error_behavior not in ("fail", "continue"):
            raise ValueError(
                f"Invalid error_behavior: {error_behavior}. Must be 'fail' or 'continue'"
            )

        self.error_behavior = error_behavior
        self.on_fail = on_fail
        self.metadata = metadata

        # Generate unique expression ID for tracking
        self._expression_id = id(self)
        self._expression_name = self._get_expression_name()

        # Log initialization
        self._log_init(**metadata)

    # =========================================================================
    # CORE EVALUATION INTERFACE
    # =========================================================================

    @final
    def evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """
        Main evaluation orchestrator - handles all infrastructure.

        This method is @final to ensure consistent behavior across all expressions.
        It provides:
        - Performance timing and logging
        - Error handling based on configured behavior
        - Fallback expression execution
        - Debug context for troubleshooting

        Storage context management is delegated to the user in do_evaluate() for
        maximum flexibility and explicit control via context managers.

        Subclasses should NOT override this method. Instead, implement do_evaluate().

        Args:
            evaluator: The evaluator providing execution environment
            context: The execution context with metadata and state
        """
        start_time = time.perf_counter()

        # Start evaluation logging
        self._log_start(evaluator, context)

        try:
            try:
                # Execute the actual expression logic
                self.do_evaluate(evaluator, context)

                # Calculate performance metrics
                duration = time.perf_counter() - start_time
                self._log_end(evaluator, context, duration)

            except Exception as eval_error:
                # Handle evaluation errors
                duration = time.perf_counter() - start_time
                self._log_error(evaluator, context, eval_error, duration)
                self._handle_error(eval_error, evaluator, context)

        except Exception as infra_error:
            # Handle infrastructure errors (logging, etc.)
            duration = time.perf_counter() - start_time
            logger.error(
                f"Infrastructure error in expression {self._expression_name}",
                extra={
                    "expression_id": self._expression_id,
                    "expression_type": type(self).__name__,
                    "duration_ms": duration * 1000,
                    "error_type": type(infra_error).__name__,
                    "error_message": str(infra_error),
                },
                exc_info=True,
            )
            raise ExpressionError(
                f"Infrastructure failure in {self._expression_name}: {infra_error}",
                expression=self,
                cause=infra_error,
            )

    @abstractmethod
    def do_evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """
        Execute the expression's core logic.

        This is the method that subclasses implement to define their behavior.
        The base class provides all infrastructure support:
        - Logging and error handling are automatic
        - Performance tracking is built-in
        - Value resolution utilities are available
        - Storage context management is explicit via context managers

        Args:
            evaluator: The evaluator providing execution environment
            context: The execution context with metadata and state

        Example:
            ```python
            def do_evaluate(self, evaluator: Evaluator, context: Context) -> None:
                # User manages storage context via context managers
                with evaluator.state.at("workspace").with_dict_view() as workspace:
                    # Resolve input values using view's storage context
                    values = self._resolve_values({
                        "operand_a": self.a,
                        "operand_b": self.b
                    }, evaluator.state, workspace.ctx)

                    # Perform calculation
                    result = values["operand_a"] + values["operand_b"]

                    # Store result using same storage context
                    if self.result_path:
                        path = self._parse_state_path(self.result_path)
                        result_view = evaluator.state.at(*path).dict_view(ctx=workspace.ctx)
                        result_view.store(result)
            ```
        """
        pass

    # =========================================================================
    # VALUE RESOLUTION UTILITIES
    # =========================================================================

    def _resolve_value(
        self,
        value: ValueOrPath[TreeValueT],
        state: "StateProtocol",
        storage_ctx: "StorageContext",
    ) -> TreeValueT:
        """
        Resolve a value that could be either a direct value or a state path.

        This is the core utility for flexible parameter handling. It allows
        expressions to accept parameters as either literal values or paths
        to values in the state tree.

        Args:
            value: Either a direct value or a string path to state
            state: State interface for path resolution
            storage_ctx: Storage context (transaction or snapshot) for consistent access

        Returns:
            Resolved value

        Raises:
            ValueResolutionError: If path resolution fails

        Examples:
            ```python
            # Direct value
            result = self._resolve_value(42, state, storage_ctx)  # Returns: 42

            # State path
            result = self._resolve_value("market.price", state, storage_ctx)  # Returns: value from state

            # Complex path
            result = self._resolve_value("users.alice.profile.email", state, storage_ctx)
            ```
        """
        try:
            if self._is_state_path(value):
                # Parse and resolve state path
                path_components = self._parse_state_path(value)

                logger.debug(
                    f"Resolving state path in {self._expression_name}",
                    extra={
                        "expression_id": self._expression_id,
                        "path": value,
                        "path_components": path_components,
                        "storage_context_type": type(storage_ctx).__name__,
                        "storage_context_id": getattr(storage_ctx, "id", "unknown"),
                    },
                )

                # Access state using storage context via lower-level interface
                resolved_value = state.at(*path_components).dict_view(ctx=storage_ctx).extract()

                logger.debug(
                    f"Successfully resolved state path in {self._expression_name}",
                    extra={
                        "expression_id": self._expression_id,
                        "path": value,
                        "resolved_type": type(resolved_value).__name__,
                    },
                )

                return resolved_value
            else:
                # Direct value - return as-is
                logger.debug(
                    f"Using direct value in {self._expression_name}",
                    extra={
                        "expression_id": self._expression_id,
                        "value_type": type(value).__name__,
                    },
                )
                return cast(TreeValueT, value)

        except Exception as e:
            raise ValueResolutionError(
                f"Failed to resolve value {value} in {self._expression_name}: {e}",
                expression=self,
                cause=e,
            )

    def _resolve_values(
        self,
        values: Dict[str, ValueOrPath[Any]],
        state: "StateProtocol",
        storage_ctx: "StorageContext",
    ) -> Dict[str, Any]:
        """
        Resolve multiple values using the same storage context for consistency.

        This ensures all values are resolved at the same point in time,
        preventing race conditions and ensuring consistent state snapshots.
        Essential for expressions that need multiple values to be coherent.

        Args:
            values: Dictionary of key -> (value or state path)
            state: State interface for path resolution
            storage_ctx: Storage context (transaction or snapshot) for consistent access

        Returns:
            Dictionary with all values resolved

        Example:
            ```python
            # Resolve multiple values consistently
            resolved = self._resolve_values({
                "price": "market.current_price",
                "volume": 1000,
                "multiplier": "config.trading.multiplier"
            }, state, storage_ctx)
            # Returns: {"price": 150.50, "volume": 1000, "multiplier": 2.5}
            # All state values resolved at the same point in time
            ```
        """
        logger.debug(
            f"Resolving multiple values in {self._expression_name}",
            extra={
                "expression_id": self._expression_id,
                "value_count": len(values),
                "keys": list(values.keys()),
                "storage_context_type": type(storage_ctx).__name__,
            },
        )

        resolved = {}
        for key, value in values.items():
            try:
                resolved[key] = self._resolve_value(value, state, storage_ctx)
            except Exception as e:
                raise ValueResolutionError(
                    f"Failed to resolve '{key}' in {self._expression_name}: {e}",
                    expression=self,
                    cause=e,
                )

        logger.debug(
            f"Successfully resolved all values in {self._expression_name}",
            extra={
                "expression_id": self._expression_id,
                "resolved_keys": list(resolved.keys()),
                "resolved_types": {k: type(v).__name__ for k, v in resolved.items()},
            },
        )

        return resolved

    def _is_state_path(self, value: Any) -> TypeGuard[str]:
        """
        Determine if a value should be treated as a state path.

        Uses TypeGuard to provide type safety - when this returns True,
        TypeScript/mypy knows the value is definitely a string.

        Current heuristic:
        - Must be a string
        - Must contain dots (indicating path structure)
        - Must not be a pure number string

        Args:
            value: Value to check

        Returns:
            True if value should be treated as state path

        Examples:
            ```python
            self._is_state_path("market.price")        # True
            self._is_state_path("config.timeouts.api") # True
            self._is_state_path("42")                  # False
            self._is_state_path("42.5")                # False
            self._is_state_path(42)                    # False
            self._is_state_path("simple")              # False
            ```
        """
        if not isinstance(value, str):
            return False

        # Simple string without dots is not a path
        if "." not in value:
            return False

        # Pure numeric strings (including decimals) are not paths
        try:
            float(value)
            return False
        except ValueError:
            pass

        return True

    def _parse_state_path(self, path: str) -> Tuple[str, ...]:
        """
        Parse a state path string into path components.

        Validates the path format and returns clean components for state navigation.
        Handles edge cases like empty components and whitespace.

        Args:
            path: Path string like "market.feeds.price"

        Returns:
            Tuple of path components

        Raises:
            ValueError: If path format is invalid

        Examples:
            ```python
            self._parse_state_path("market.price")         # ("market", "price")
            self._parse_state_path("users.alice.profile")  # ("users", "alice", "profile")
            self._parse_state_path("config")               # ("config",)
            ```
        """
        if not isinstance(path, str):
            raise ValueError(f"State path must be string, got {type(path).__name__}")

        if not path.strip():
            raise ValueError("State path cannot be empty")

        # Split on dots and filter empty components
        components = tuple(component.strip() for component in path.split(".") if component.strip())

        if not components:
            raise ValueError(f"Invalid state path format: '{path}'")

        return components

    # =========================================================================
    # LOGGING INFRASTRUCTURE
    # =========================================================================

    def _log_init(self, **extra_context) -> None:
        """Log expression initialization with metadata."""
        logger.debug(
            f"Initialized expression {self._expression_name}",
            extra={
                "expression_id": self._expression_id,
                "expression_type": type(self).__name__,
                "error_behavior": self.error_behavior,
                "has_on_fail": self.on_fail is not None,
                **extra_context,
            },
        )

    def _log_start(self, evaluator: "Evaluator", context: "Context") -> None:
        """Log evaluation start with context."""
        logger.info(
            f"Starting evaluation of {self._expression_name}",
            extra={
                "expression_id": self._expression_id,
                "expression_type": type(self).__name__,
                "context_attributes": list(context.attributes.keys()) if context.attributes else [],
                "evaluator_id": id(evaluator),
            },
        )

    def _log_end(self, evaluator: "Evaluator", context: "Context", duration: float) -> None:
        """Log successful evaluation completion."""
        logger.info(
            f"Completed evaluation of {self._expression_name}",
            extra={
                "expression_id": self._expression_id,
                "expression_type": type(self).__name__,
                "duration_ms": duration * 1000,
                "success": True,
            },
        )

    def _log_error(
        self, evaluator: "Evaluator", context: "Context", error: Exception, duration: float
    ) -> None:
        """Log evaluation error with full context."""
        logger.error(
            f"Expression {self._expression_name} failed",
            extra={
                "expression_id": self._expression_id,
                "expression_type": type(self).__name__,
                "duration_ms": duration * 1000,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_behavior": self.error_behavior,
                "will_execute_on_fail": self.on_fail is not None,
            },
            exc_info=True,
        )

    # =========================================================================
    # ERROR HANDLING & RECOVERY
    # =========================================================================

    def _handle_error(self, error: Exception, evaluator: "Evaluator", context: "Context") -> None:
        """
        Handle evaluation errors based on configured behavior.

        Executes fallback expressions and determines whether to fail or continue
        based on the configured error behavior.

        Args:
            error: The exception that occurred
            evaluator: Evaluator instance
            context: Execution context
        """
        # Execute on_fail expression if configured
        if self.on_fail is not None:
            try:
                logger.info(
                    f"Executing on_fail expression for {self._expression_name}",
                    extra={
                        "expression_id": self._expression_id,
                        "on_fail_type": type(self.on_fail).__name__,
                    },
                )
                self.on_fail.evaluate(evaluator, context)
            except Exception as fail_error:
                logger.error(
                    f"on_fail expression failed for {self._expression_name}",
                    extra={
                        "expression_id": self._expression_id,
                        "original_error": str(error),
                        "fail_error": str(fail_error),
                    },
                    exc_info=True,
                )

        # Handle based on error behavior
        if self.error_behavior == "fail":
            # Re-raise the original error
            raise error
        elif self.error_behavior == "continue":
            # Log and continue execution
            logger.warning(
                f"Continuing after error in {self._expression_name}",
                extra={"expression_id": self._expression_id, "error_type": type(error).__name__},
            )
        # If we reach here with "continue", the error is swallowed and execution continues

    # =========================================================================
    # METADATA & INTROSPECTION
    # =========================================================================

    def _get_expression_name(self) -> str:
        """Get human-readable expression name for logging."""
        return type(self).__name__

    def _get_expression_metadata(self) -> Dict[str, Any]:
        """Get expression metadata for debugging/introspection."""
        return {
            "id": self._expression_id,
            "name": self._expression_name,
            "type": type(self).__name__,
            "error_behavior": self.error_behavior,
            "has_on_fail": self.on_fail is not None,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self._expression_name}(id={self._expression_id}, error_behavior={self.error_behavior})"
