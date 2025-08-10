"""
Updated Expression Base Class with Structural Path Support

Provides deterministic, hierarchical identification for expressions
enabling resumable and distributed execution through structural paths.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar, cast, final

from loomi._tree.path import ExtendedPath, Path, PathResolver
from loomi._tree.query import Query
from loomi._tree.tree import BaseView, Tree
from loomi._tree.tree.types import Value

from .context import Context
from .exceptions import ExpressionError, ValueResolutionError
from .logger import logger
from .structural_path import create_component
from .types import ErrorBehavior, ExpressionPath, ExpressionValue, StorageContext

AppT = TypeVar("AppT")


class Expression(ABC, Generic[AppT]):
    """
    Enhanced base class for all Loomi expressions with structural path support.

    Provides comprehensive foundation for building production-ready expressions
    with deterministic structural identification. The base class handles all
    infrastructure concerns, allowing subclasses to focus purely on business logic.

    Structural Features:
    - Automatic structural component generation based on class hierarchy
    - Deterministic path building for resumable execution
    - Clean child context creation with explicit index support
    - Integration with distributed state through structural keys

    Args:
        error_behavior: How to handle errors ("fail" or "continue")
        on_fail: Optional expression to execute when errors occur

    Example:
        ```python
        class ProcessData(Expression):
            def do_evaluate(self, context: Context) -> None:
                for i, child_expr in enumerate(self.children):
                    # Clean child context creation with explicit indexing
                    child_context = self._create_child_context(
                        context, child_expr, child_index=i
                    )
                    child_expr.evaluate(child_context)
        ```
    """

    def __init__(
        self,
        app: AppT,
        /,
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
            name: Optional name for debugging (does not affect structural path)
            **metadata: Additional metadata for debugging and introspection
        """
        # Validate error behavior
        if error_behavior not in ("fail", "continue"):
            raise ValueError(
                f"Invalid error_behavior: {error_behavior}. Must be 'fail' or 'continue'"
            )

        self._app = app
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
    def app(self) -> AppT:
        """Get the app instance this expression belongs to."""
        return self._app

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
    def evaluate(self, context: "Context | None" = None) -> None:
        """
        Main evaluation orchestrator - handles all infrastructure.

        This method is @final to ensure consistent behavior across all expressions.
        It provides:
        - Performance timing and logging
        - Error handling based on configured behavior
        - Fallback expression execution
        - Debug context for troubleshooting
        - Structural path validation

        Subclasses should NOT override this method. Instead, implement do_evaluate().

        Args:
            context: The execution context with structural path information
        """
        start_time = time.perf_counter()

        context = context or Context()

        # Start evaluation logging
        self._log_start(context)

        try:
            try:
                # Execute the actual expression logic
                self.do_evaluate(context)

                # Calculate performance metrics
                duration = time.perf_counter() - start_time
                self._log_end(context, duration)

            except Exception as eval_error:
                # Handle evaluation errors
                duration = time.perf_counter() - start_time
                self._log_error(context, eval_error, duration)
                self._handle_error(eval_error, context)

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
                    "structural_path": str(context.structural_path),
                },
                exc_info=True,
            )
            raise ExpressionError(
                f"Infrastructure failure in {self.readable_name}: {infra_error}",
                expression=self,
                cause=infra_error,
            )

    @abstractmethod
    def do_evaluate(self, context: "Context") -> None:
        """
        Execute the expression's core logic.

        This is the method that subclasses implement to define their behavior.
        The base class provides all infrastructure support including structural
        path management and child context creation utilities.

        Args:
            context: The execution context with structural path information

        Example:
            ```python
            def do_evaluate(self, context: Context) -> None:
                # Process multiple children with explicit indexing
                for i, child_expr in enumerate(self.child_expressions):
                    child_context = self._create_child_context(
                        context, child_expr, child_index=i
                    )
                    child_expr.evaluate(child_context)

                # Or single child without index
                child_context = self._create_child_context(context, single_child)
                single_child.evaluate(child_context)
            ```
        """
        raise NotImplementedError("do_evaluate() must be implemented by subclasses")

    # =========================================================================
    # STRUCTURAL PATH UTILITIES
    # =========================================================================

    def _create_child_context(
        self,
        context: "Context",
        child_expression: "Expression",
        child_index: int | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> "Context":
        """
        Create a child context with proper structural path extension.

        This is the primary method users call to create contexts for child expressions.
        It automatically generates deterministic structural components and extends
        the structural path appropriately.

        Args:
            context: The parent context
            child_expression: The child expression to create context for
            child_index: Optional index for disambiguating multiple instances
            attributes: Additional attributes for the child context

        Returns:
            A new child context with extended structural path

        Example:
            ```python
            # Single child (no index needed)
            child_ctx = self._create_child_context(context, processor)

            # Multiple children of same type (index required)
            for i, worker in enumerate(workers):
                child_ctx = self._create_child_context(
                    context, worker, child_index=i
                )
            ```
        """
        # Generate child's structural component
        child_component = create_component(child_expression, child_index)

        child_context = context.create_child_context(
            child_component=child_component,
            attributes=attributes,
        )

        logger.debug(
            f"Created child context for {child_expression.readable_name}",
            extra={
                "parent_path": str(context.structural_path),
                "child_component": child_component,
                "child_path": str(child_context.structural_path),
                "child_index": child_index,
            },
        )

        return child_context

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
        """
        try:
            if isinstance(value, Query):
                logger.debug(
                    f"Resolving state expression: {value}",
                    extra={
                        "value_type": type(value).__name__,
                        "structural_path": str(context.structural_path),
                    },
                )
                return value.evaluate(state, storage_ctx, cast(dict, context.attributes))
            elif isinstance(value, (Path, ExtendedPath)):
                logger.debug(
                    f"Resolving state expression: {value}",
                    extra={
                        "value_type": type(value).__name__,
                        "structural_path": str(context.structural_path),
                    },
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

    def _log_start(self, context: "Context") -> None:
        """Log evaluation start with context."""
        logger.info(
            f"Starting evaluation of {self.readable_name}",
            extra={
                "expression_type": type(self).__name__,
                "context_attributes": list(context.attributes.keys()) if context.attributes else [],
                "structural_path": str(context.structural_path),
                "structural_key": context.structural_key,
            },
        )

    def _log_end(self, context: "Context", duration: float) -> None:
        """Log successful evaluation completion."""
        logger.info(
            f"Completed evaluation of {self.readable_name}",
            extra={
                "expression_type": type(self).__name__,
                "duration_ms": duration * 1000,
                "success": True,
                "structural_path": str(context.structural_path),
            },
        )

    def _log_error(self, context: "Context", error: Exception, duration: float) -> None:
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
                "structural_path": str(context.structural_path),
            },
            exc_info=True,
        )

    # =========================================================================
    # ERROR HANDLING & RECOVERY
    # =========================================================================

    def _handle_error(self, error: Exception, context: "Context") -> None:
        """
        Handle evaluation errors based on configured behavior.

        Executes fallback expressions and determines whether to fail or continue
        based on the configured error behavior.

        Args:
            error: The exception that occurred
            context: Execution context
        """
        # Execute on_fail expression if configured
        if self.on_fail is not None:
            try:
                logger.info(
                    f"Executing on_fail expression for {self.readable_name}",
                    extra={
                        "on_fail_type": type(self.on_fail).__name__,
                        "structural_path": str(context.structural_path),
                    },
                )
                # Create child context for on_fail execution
                fail_context = self._create_child_context(context, self.on_fail)
                self.on_fail.evaluate(fail_context)
            except Exception as fail_error:
                logger.error(
                    f"on_fail expression failed for {self.readable_name}",
                    extra={
                        "original_error": str(error),
                        "fail_error": str(fail_error),
                        "structural_path": str(context.structural_path),
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
                extra={
                    "error_type": type(error).__name__,
                    "structural_path": str(context.structural_path),
                },
            )

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
