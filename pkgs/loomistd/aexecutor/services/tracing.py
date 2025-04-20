"""
Tracing service for the operations framework.

This module implements the TracingService, which provides tracing and
observability for operation execution.
"""

from loomi.service import AsyncService
from loomi.spec import Spec, SpecField


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


class TracingServiceSpec(Spec):
    """
    Specification for the TracingService.

    This specification defines the configuration and dependencies for the
    TracingService.
    """

    name: str = SpecField(default="tracing_service")
    factory: type = SpecField(default=TracingService)
