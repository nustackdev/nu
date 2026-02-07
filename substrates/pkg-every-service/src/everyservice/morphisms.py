"""ServiceMethodCall -- morphism for calling service methods.

Parallel to ItemGetOp for documents. The interface provides resolve(ctx)
to get the service instance, then the named method is called with resolved
arguments.
"""

from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

from everybase import INVALID, Command, Morphism, Sentinel, is_sentinel


if TYPE_CHECKING:
    from everybase import Context

    from .interface import Interface


__all__ = [
    "ServiceMethodCall",
]


class ServiceMethodCall[T](Command, Morphism[T | Sentinel]):
    """Call a method on a service resolved from Context.

    Parallel to ItemGetOp for documents. The interface provides
    resolve(ctx) to get the service instance. Args and kwargs are
    lazy Terms executed before the service call.

    Sentinel propagation: if any argument resolves to a sentinel
    (EMPTY, INVALID), returns INVALID without calling the service.

    Usage::

        ServiceMethodCall(my_interface, "get_balance", pubkey_term)
        ServiceMethodCall(my_interface, "search", query=query_term, limit=10)
    """

    def __init__(
        self, interface: Interface, method_name: str, *args: object, **kwargs: object
    ) -> None:
        """Initialize service method call.

        Args:
            interface: The Interface that provides service resolution.
            method_name: Name of the method to call on the service.
            *args: Positional arguments (can be Terms or literals).
            **kwargs: Keyword arguments (can be Terms or literals).
        """
        super().__init__(*args, *kwargs.values())
        self._interface = interface
        self._method_name = method_name
        self._kwarg_keys = tuple(kwargs.keys())

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Execute the service method call.

        Resolves all argument Terms first (propagating sentinels),
        then resolves the service from Context via the interface,
        calls the named method, and awaits if async.

        Args:
            ctx: Execution context.

        Returns:
            Result of the service method call, or INVALID on sentinel args.
        """
        # Resolve args with sentinel propagation
        values = []
        for child in self.children:
            val = await child.execute(ctx)
            if is_sentinel(val):
                return INVALID
            values.append(val)

        # Split back into positional and keyword args
        num_kwargs = len(self._kwarg_keys)
        if num_kwargs:
            args = values[:-num_kwargs]
            kwargs = dict(zip(self._kwarg_keys, values[-num_kwargs:], strict=True))
        else:
            args = values
            kwargs = {}

        service = self._interface.resolve(ctx)
        result = getattr(service, self._method_name)(*args, **kwargs)
        if isawaitable(result):
            result = await result
        return result

    def __repr__(self) -> str:
        """String representation."""
        iface = self._interface.__class__.__name__
        parts = [repr(c) for c in self._children]

        # Annotate kwargs with their keys
        num_kwargs = len(self._kwarg_keys)
        if num_kwargs:
            positional = parts[:-num_kwargs]
            kw_values = parts[-num_kwargs:]
            kw_parts = [f"{k}={v}" for k, v in zip(self._kwarg_keys, kw_values, strict=True)]
            all_parts = positional + kw_parts
        else:
            all_parts = parts

        args_str = ", ".join(all_parts)
        if args_str:
            return f"ServiceMethodCall({iface}.{self._method_name}, {args_str})"
        return f"ServiceMethodCall({iface}.{self._method_name})"
