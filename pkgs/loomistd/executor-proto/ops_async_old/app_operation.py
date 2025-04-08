from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol


class AppOperation(BaseOperation):
    """Wraps an app as an operation."""

    def __init__(self, app: "AsyncApp", /, *, path: tuple[str, ...] | None = None) -> None:
        if not app:
            raise ValueError("Appoperation requires an app")

        self.child_app = app
        self.path = path
        self._id = hex(id(self))[2:]

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the wrapped function."""
        logger.info(f"Executing function: {self.child_app.readable_name}")

        app_loc = loc
        if self.path and len(self.path) > 0:
            app_loc = await loc.dict(*self.path)

        try:
            try:
                await self.child_app.execute(
                    await self.child_app.run(self.context, app_loc), app_loc
                )
                logger.info(f"Operation '{self.child_app.readable_name}' completed successfully")

            except Exception as e:
                error_msg = f"Operation '{self.child_app.readable_name}' failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise OperationError(error_msg) from e

        except asyncio.CancelledError:
            logger.info(f"Operation '{self.child_app.readable_name}' was cancelled")
            raise

        except Exception as e:
            if not isinstance(e, OperationError):
                logger.error(f"Operation '{self.child_app.readable_name}' failed", exc_info=True)
                raise OperationError(f"App operation failed: {str(e)}") from e
            raise
