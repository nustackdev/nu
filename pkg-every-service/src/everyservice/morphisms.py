"""ServiceMethodCall -- morphism for calling service methods.

Parallel to ItemGetOp for documents. The interface provides resolve(ctx)
to get the service instance, then the named method is called with resolved
arguments.
"""

from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from everybase import Command, Morphism


if TYPE_CHECKING:
    from everybase import Context

    from .interface import Interface


__all__ = [
    "ServiceMethodCall",
]


class ServiceMethodCall[T](Command, Morphism[T]):
    """Call a method on a service resolved from Context.

    Parallel to ItemGetOp for documents. The interface provides
    resolve(ctx) to get the service instance. Args are lazy Terms
    executed before the service call.

    Usage::

        ServiceMethodCall(my_interface, "get_balance", pubkey_term)
    """

    def __init__(self, interface: Interface, method_name: str, *args: object) -> None:
        """Initialize service method call.

        Args:
            interface: The Interface that provides service resolution.
            method_name: Name of the method to call on the service.
            *args: Arguments to the method (can be Terms or literals).
        """
        super().__init__(*args)
        self._interface = interface
        self._method_name = method_name

    async def execute(self, ctx: Context) -> T:
        """Execute the service method call.

        Resolves the service from Context via the interface, executes
        all argument Terms, then calls the named method. Awaits the
        result if the method is async.

        Args:
            ctx: Execution context.

        Returns:
            Result of the service method call.
        """
        service = self._interface.resolve(ctx)
        args = [await c.execute(ctx) for c in self.children]
        result = getattr(service, self._method_name)(*args)
        if isawaitable(result):
            result = await result
        return result

    def __repr__(self) -> str:
        """String representation."""
        args = ", ".join(repr(c) for c in self._children)
        iface = self._interface.__class__.__name__
        if args:
            return f"ServiceMethodCall({iface}.{self._method_name}, {args})"
        return f"ServiceMethodCall({iface}.{self._method_name})"
