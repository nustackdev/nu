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
from typing import TYPE_CHECKING, Any, Dict, Optional, cast, final

from loomi._behaviors.state.path import ExtendedPath, Path, PathResolver
from loomi._behaviors.state.query import Query
from loomi._behaviors.state.tree import BaseView, Tree
from loomi._behaviors.state.tree.types import Value

from .exceptions import ExpressionError, ValueResolutionError
from .logger import logger
from .types import ErrorBehavior, ExpressionPath, ExpressionValue, StorageContext

if TYPE_CHECKING:
    from loomi._behaviors.evaluator import Context, Evaluator


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
        name: Optional[str] = None,
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

        self._error_behavior = error_behavior
        self._on_fail = on_fail
        self._name = name
        self._metadata = metadata

        self._log_init(**metadata)

    @property
    def readable_name(self) -> str:
        """Get a human-readable name for the expression."""
        return self._name or type(self).__name__

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def error_behavior(self) -> str:
        """Get the configured error behavior for this expression."""
        return self._error_behavior

    @property
    def on_fail(self) -> Optional["Expression"]:
        """Get the fallback expression to execute on error."""
        return self._on_fail

    @property
    def info(self) -> Dict[str, Any]:
        """Get expression metadata for debugging/introspection."""
        info = {
            "type": type(self).__name__,
            "error_behavior": self.error_behavior,
            "has_on_fail": self.on_fail is not None,
            "metadata": self._metadata,
        }
        if self.name:
            info["name"] = self.name
        return info

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
                f"Infrastructure error in expression {self.readable_name}",
                extra={
                    "expression_type": type(self).__name__,
                    "duration_ms": duration * 1000,
                    "error_type": type(infra_error).__name__,
                    "error_message": str(infra_error),
                },
                exc_info=True,
            )
            raise ExpressionError(
                f"Infrastructure failure in {self.readable_name}: {infra_error}",
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
        raise NotImplementedError("do_evaluate() must be implemented by subclasses")

    # =========================================================================
    # VALUE RESOLUTION UTILITIES
    # =========================================================================

    def _resolve_path(
        self,
        path: ExpressionPath,
        state: "Tree",
        storage_ctx: "StorageContext",
        context: "Context",
    ) -> tuple[BaseView, str | int]:
        """
        Resolve a path that could be a string or Path object.

        This utility allows expressions to accept parameters as either
        literal values or paths to values in the state tree. It abstracts
        away the complexity of path resolution, providing a consistent
        interface for all expressions.

        Args:
            path: The path to resolve
            state: The state tree for resolution
            storage_ctx: The storage context for view management

        Returns:
            The resolved view for the path
        """
        last_component: str | int | None

        path = self._process_path(path, context)

        if path.is_root():
            raise ValueResolutionError("Cannot resolve root path as a view")

        path_resolver = PathResolver()
        parent_view = path_resolver.parent_view(path, state, storage_ctx)
        last_component = path.last_component()

        if last_component is None:
            raise ValueResolutionError("Path must have a last component to resolve")

        return parent_view, last_component

    def _resolve_value(
        self,
        value: ExpressionValue,
        state: "Tree",
        storage_ctx: "StorageContext",
        context: "Context",
    ) -> Value:
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
            if isinstance(value, Query):
                logger.debug(
                    f"Resolving state expression: {value}",
                    extra={"value_type": type(value).__name__},
                )
                return value.evaluate(state, storage_ctx, cast(dict, context.attributes))
            elif isinstance(value, (Path, ExtendedPath)):
                logger.debug(
                    f"Resolving state expression: {value}",
                    extra={"value_type": type(value).__name__},
                )
                value = self._process_path(value, context)
                return value.resolve(state, storage_ctx, cast(dict, context.attributes))
            else:
                return cast(Value, value)

        except Exception as e:
            raise ValueResolutionError(
                f"Failed to resolve value {value} in {self.readable_name}: {e}",
                expression=self,
                cause=e,
            )

    def _resolve_values(
        self,
        values: dict[str, ExpressionValue],
        state: "Tree",
        storage_ctx: "StorageContext",
        context: "Context",
    ) -> dict[str, Value]:
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
        resolved = {}
        for key, value in values.items():
            try:
                resolved[key] = self._resolve_value(value, state, storage_ctx, context)
            except Exception as e:
                raise ValueResolutionError(
                    f"Failed to resolve '{key}' in {self.readable_name}: {e}",
                    expression=self,
                    cause=e,
                )

        return resolved

    def _process_path(self, path: ExpressionPath, context: "Context") -> Path:
        """
        Process a path expression into a Path object.

        This utility method ensures that the path is correctly interpreted
        as a Path object, allowing for consistent handling of state paths.

        Args:
            evaluator: The evaluator providing execution environment
            context: The execution context with metadata and state
            path: The path expression to process

        Returns:
            A Path object representing the processed path expression
        """
        # Convert path to list of components to then inject Context values
        if isinstance(path, str):
            list_path = path.split(".")
            # Convert integers in path to int
            list_path = [
                int(i) if i.isdigit() or (i.startswith("-") and i[1:].isdigit()) else i
                for i in list_path
            ]
            return Path(tuple(list_path))
        elif isinstance(path, tuple):
            return Path(tuple(path))
        elif isinstance(path, Path):
            return path
        elif isinstance(path, ExtendedPath):
            return path.substitute_variables(cast(dict, context.attributes))

        raise ValueResolutionError(
            f"Invalid path type: {type(path).__name__}. Must be str, tuple, or Path"
        )

    # =========================================================================
    # LOGGING INFRASTRUCTURE
    # =========================================================================

    def _log_init(self, **extra_context) -> None:
        """Log expression initialization with metadata."""
        logger.debug(
            f"Initialized expression {self.readable_name}",
            extra={
                "expression_type": type(self).__name__,
                "error_behavior": self.error_behavior,
                "has_on_fail": self.on_fail is not None,
                **extra_context,
            },
        )

    def _log_start(self, evaluator: "Evaluator", context: "Context") -> None:
        """Log evaluation start with context."""
        logger.info(
            f"Starting evaluation of {self.readable_name}",
            extra={
                "expression_type": type(self).__name__,
                "context_attributes": list(context.attributes.keys()) if context.attributes else [],
                "evaluator_id": id(evaluator),
            },
        )

    def _log_end(self, evaluator: "Evaluator", context: "Context", duration: float) -> None:
        """Log successful evaluation completion."""
        logger.info(
            f"Completed evaluation of {self.readable_name}",
            extra={
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
            f"Expression {self.readable_name} failed",
            extra={
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
                    f"Executing on_fail expression for {self.readable_name}",
                    extra={
                        "on_fail_type": type(self.on_fail).__name__,
                    },
                )
                self.on_fail.evaluate(evaluator, context)
            except Exception as fail_error:
                logger.error(
                    f"on_fail expression failed for {self.readable_name}",
                    extra={
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
                f"Continuing after error in {self.readable_name}",
                extra={"error_type": type(error).__name__},
            )
        # If we reach here with "continue", the error is swallowed and execution continues

    # =========================================================================
    # METADATA & INTROSPECTION
    # =========================================================================

    def __repr__(self) -> str:
        """String representation for debugging."""
        info_str = ", ".join(f"{k}={v!r}" for k, v in self.info.items() if k != "metadata")

        # Add metadata separately if it exists, with better formatting
        if self.info.get("metadata"):
            metadata_str = ", ".join(f"{k}={v!r}" for k, v in self.info["metadata"].items())
            info_str += f", metadata={{{metadata_str}}}"

        return f"{self.readable_name}({info_str})"
