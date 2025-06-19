"""
App expression.

This module provides the App expression, which executes a Loomi app
as an expression.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Tuple, Union, cast

from loomi.app import AsyncApp, SyncApp
from loomi.interfaces.executor.operations import AppOperationProtocol
from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateT

from ..base import Expression
from ..metadata import ExpressionMetadata

if TYPE_CHECKING:
    from ...context import Context

__all__ = [
    "App",
]


class App(Expression[StateT]):
    """
    Executes a Loomi app as an expression.

    This expression adapts a Loomi app to the expressions framework,
    allowing apps to be composed within workflows.

    Args:
        app: The app to execute
        state_path: Optional path to mount the app's state
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> from loomi import AsyncApp
        >>> my_app = AsyncApp()
        >>> expr = App(my_app, state_path=("apps", "my_app"))
    """

    def __init__(
        self,
        app: Union[AsyncApp, SyncApp],
        /,
        *,
        state_path: Optional[Union[Tuple[str, ...], str]] = None,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression[StateT]] = None,
    ):
        """
        Initialize the App expression.

        Args:
            app: The app to execute
            state_path: Optional path to mount the app's state
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            OperationConfigError: If app is not a valid Loomi app
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        self._app = app

        # Process state_path
        self._state_path: Optional[Tuple[str, ...]] = None
        if isinstance(state_path, str):
            self._state_path = (state_path,)
        elif isinstance(state_path, tuple):
            self._state_path = state_path

        app_expression = cast(Expression[StateT], self._app.define())

        self.children = (app_expression,)

    @property
    def app(self) -> Union[AsyncApp, SyncApp]:
        """
        Get the app to execute.

        Returns:
            The Loomi app
        """
        return self._app

    @property
    def state_path(self) -> Optional[Tuple[str, ...]]:
        """
        Get the state path where the app will be mounted.

        Returns:
            The state path or None if using current context's path
        """
        return self._state_path

    @property
    def metadata(self) -> ExpressionMetadata:
        """
        Get the expression's metadata.

        Includes the app class or name in the metadata.

        Returns:
            The expression metadata
        """
        metadata = super().metadata

        custom_properties: dict[str, Any] = {}
        try:
            app_name = getattr(self._app, "__class__", self._app).__name__
            custom_properties["app"] = app_name

            if self._state_path:
                custom_properties["state_path"] = self._state_path

        except Exception:
            # In case of error, just use the default metadata
            pass

        return metadata.with_properties(**custom_properties)


if TYPE_CHECKING:
    _: type[AppOperationProtocol[Expression, "Context"]] = App
