"""Interface -- base class for service definitions.

Each service gets an Interface subclass. Methods return lazy Value terms,
not live results. The interface provides resolve(ctx) to get the service
instance from Context at execution time.

With the method descriptor, definitions become declarative one-liners::

    class SolanaRpc(Interface):
        _service_type = SolanaRpcClient
        get_latest_blockhash = method(StrValue)
        get_balance = method(IntValue, "getBalance")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from everybase import Model

from .morphisms import ServiceMethodCall


if TYPE_CHECKING:
    from everybase import Context
    from everybase.abc.values import ValueBase


__all__ = [
    "Interface",
]


class Interface(Model):
    """Base for service interface definitions.

    Subclass per service. Use ``method()`` descriptors for declarative
    method binding, or call ``self.call()`` directly for dynamic dispatch.

    Usage::

        class SolanaRpc(Interface):
            _service_type = SolanaRpcClient

            get_latest_blockhash = method(StrValue)
            get_balance = method(IntValue, "getBalance")

    At execution time::

        ctx = Context().with_handle(SolanaRpcClient, client_instance)
        result = await rpc.get_balance(pubkey).execute(ctx)
    """

    _service_type: ClassVar[type]

    def call[V: ValueBase](
        self, value_type: type[V], method_name: str, *args: object, **kwargs: object
    ) -> V:
        """Build a lazy Value term for a service method call.

        Args:
            value_type: The Value class to wrap the result in.
            method_name: Name of the method on the service.
            *args: Positional arguments (can be Terms or literals).
            **kwargs: Keyword arguments (can be Terms or literals).

        Returns:
            A Value term that, when executed, calls the service method.
        """
        return value_type(ServiceMethodCall(self, method_name, *args, **kwargs))

    def resolve(self, ctx: Context) -> Any:  # noqa: ANN401
        """Resolve the service instance from Context.

        Args:
            ctx: Execution context containing the service handle.

        Returns:
            The service instance registered for this interface's _service_type.

        Raises:
            LookupError: If no handle for _service_type in context.
        """
        return ctx.get(self._service_type)
