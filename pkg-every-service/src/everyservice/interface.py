"""Interface -- base class for service definitions.

Each service gets an Interface subclass. Methods return lazy Value terms,
not live results. The interface provides resolve(ctx) to get the service
instance from Context at execution time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from everybase import Model


if TYPE_CHECKING:
    from everybase import Context


__all__ = [
    "Interface",
]


class Interface(Model):
    """Base for service interface definitions.

    Subclass per service. Define methods that return Value terms wrapping
    ServiceMethodCall. The _service_type class var determines which handle
    is resolved from Context at execution time.

    Usage::

        class MyApiInterface(Interface):
            _service_type = MyApiClient

            def get_data(self, key: StrArg) -> DictValue:
                return DictValue(ServiceMethodCall(self, "get_data", key))

    At execution time::

        ctx = Context().with_handle(MyApiClient, client_instance)
        result = await get_data_term.execute(ctx)
    """

    _service_type: ClassVar[type]

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
