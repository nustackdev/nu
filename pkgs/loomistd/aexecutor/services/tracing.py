"""
Tracing service for the operations framework.

This module implements the TracingService, which provides tracing and
observability for operation execution.
"""

from loomi._service import AsyncService


class TracingService(AsyncService):
    """
    Service for tracing operation execution.

    Provides methods for recording trace events and retrieving trace information.
    """

    async def setup(self) -> None:
        """Initialize the tracing service."""
        pass

    async def cleanup(self) -> None:
        """Shutdown the tracing service."""
        pass
