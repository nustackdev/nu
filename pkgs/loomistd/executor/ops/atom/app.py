"""
App operation.

This module provides the App operation, which executes a Loomi app
as an operation.
"""

from __future__ import annotations

from typing import Any

from loomi.app import AsyncApp

from ...context import Context
from ...types import error_behaviors
from ..base import Operation
from ..metadata import OperationMetadata

__all__ = [
    "App",
]


class App(Operation):
    """
    Executes a Loomi app as an operation.

    This operation adapts a Loomi app to the operations framework,
    allowing apps to be composed within workflows.

    Args:
        app: The app to execute
        state_path: Optional path to mount the app's state
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> from loomi.app import App as LApp
        >>> my_app = LApp()
        >>> op = App(my_app, state_path=("apps", "my_app"))
    """

    def __init__(
        self,
        app: "AsyncApp",
        /,
        *,
        state_path: tuple[str, ...] | str | None = None,
        error_behavior: error_behaviors = "fail",
        on_fail: Operation | None = None,
    ):
        """
        Initialize the App operation.

        Args:
            app: The app to execute
            state_path: Optional path to mount the app's state
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            OperationConfigError: If app is not a valid Loomi app
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        self._app = app
        self._state_path = state_path

        # Process state_path
        if isinstance(self._state_path, str):
            self._state_path = (self._state_path,)

    @property
    def metadata(self) -> OperationMetadata:
        """
        Get the operation's metadata.

        Includes the app class or name in the metadata.

        Returns:
            The operation metadata
        """
        metadata = super().metadata

        try:
            app_name = getattr(self._app, "__class__", self._app).__name__

            custom_properties: dict[str, Any] = {"app": app_name}
            if self._state_path:
                custom_properties["state_path"] = self._state_path
        except Exception:
            # In case of error, just use the default metadata
            pass
        return metadata.with_properties(**custom_properties)

    async def _execute(self, context: Context) -> None:
        """
        Execute the app with the provided context.

        If a state_path is provided, the app's state will be mounted at that path.
        Otherwise, it will use the current context's state.

        Args:
            context: Execution context providing access to state and services

        Raises:
            StateAccessError: If the state_path cannot be accessed
        """
        pass
        # # Get app state
        # if self._state_path:
        #     try:
        #         app_state = await context.scoped.dict(*self._state_path)
        #     except Exception as e:
        #         raise StateAccessError(
        #             f"Failed to access state path {self._state_path}",
        #             operation=self,
        #             context=context,
        #             state_path=self._state_path,
        #             cause=e,
        #         )
        # else:
        #     app_state = context.state

        # # Log app execution
        # app_name = getattr(self._app, "__class__", self._app).__name__
        # logger.debug(f"Executing app {app_name}")

        # # Execute the app
        # await self._app.execute(app_state)
