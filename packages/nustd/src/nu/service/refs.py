"""Service MethodRefs: one Ref class per canonical Nu kind.

QueryRef         (ScalarQuery)   — pure scalar read.
StreamQueryRef   (StreamQuery)   — pure stream read.
ActionRef        (ScalarAction)  — mutating scalar call, yields a value.
StreamActionRef  (StreamAction)  — mutating stream call, yields items.
CommandRef       (Command)       — mutating void call, yields nothing.

All five share one declaration shape. `.method(name=..., **defaults)` does not
return a Ref: it returns a `Method` declaration, which `ServiceMeta` replaces
with a descriptor when the Service class is created. Reading the field back off
the Service class runs that descriptor and hands out a fresh Ref carrying the
endpoint address; calling the Ref builds the matching interaction. The return
annotation on `.method` says the Ref subclass so a type checker resolves
`Calc.add(...)` to the Ref's `__call__`; at runtime it is a `Method`.

`name=` names the attribute to fetch on the target object; when omitted the
descriptor's field name on the Service class is used. `**defaults` are call
kwargs baked into the endpoint, merged under whatever the call passes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.service import Method, MethodRef
from nu.forms import Dict

from .interactions import (
    ServiceAction,
    ServiceCommand,
    ServiceQuery,
    ServiceStreamAction,
    ServiceStreamQuery,
)


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = [
    "ActionRef",
    "CommandRef",
    "QueryRef",
    "StreamActionRef",
    "StreamQueryRef",
]


class QueryRef(MethodRef):
    """Read-only scalar endpoint on the Python object a Service is bound to.

    Notes:
        - Nothing resolves while the Service class body runs. The attribute is
          fetched off the ``ServiceFabric`` bound for the owning Service at the
          moment the interaction evaluates, so a wrong name fails at run.
        - The address travels as Ref payload, not as children: target attribute
          name, owning Service class, and the endpoint defaults.
        - Read-only, so the Ref binds as READ in the effect walk and the
          endpoint is never reported as writing the fabric.
        - The target method may be plain or ``async def``; an awaitable return
          is refused under ``nu.run`` and awaited under ``nu.arun``.

    Example:
        class Calc(nu.Service):
            add = nu.service.QueryRef.method()
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=nu.print(Calc.add(a=1, b=2)),
        )
    """

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> QueryRef:  # type: ignore[override]
        """Declare a read-only scalar endpoint in a Service class body.

        Args:
            name: attribute to fetch on the target. Defaults to the field name
                the declaration is assigned to on the Service class.
            defaults: call kwargs baked into the endpoint; a kwarg passed at
                the call site overrides the one declared here.

        Yields:
            A ``Method`` declaration, despite the annotation. ``ServiceMeta``
            turns it into a descriptor that yields a ``QueryRef`` on access.
        """
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the ServiceQuery that calls this endpoint with the given kwargs.

        Notes:
            - Kwargs are wrapped in a ``Dict`` child, so each value can be a Nu
              term evaluated at run rather than a fixed literal.

        Yields:
            An unevaluated interaction. Nothing is dispatched until the tree runs.
        """
        return ServiceQuery(self, Dict.of(**kwargs))


class StreamQueryRef(MethodRef):
    """Read-only stream endpoint on the Python object a Service is bound to.

    Notes:
        - The target may return any iterable, a generator, or (async only) an
          async generator; all three are bridged to the stream shape Nu expects.
        - Under ``nu.run`` an async generator return is refused; under
          ``nu.arun`` a sync iterable is wrapped so it can be pulled with
          ``async for``.
        - Read-only, so the Ref binds as READ in the effect walk.

    Example:
        class Calc(nu.Service):
            squares = nu.service.StreamQueryRef.method(name="range")
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=nu.print(nu.Collect(Calc.squares(n=4))),
        )
    """

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> StreamQueryRef:  # type: ignore[override]
        """Declare a read-only stream endpoint in a Service class body.

        Args:
            name: attribute to fetch on the target. Defaults to the field name
                the declaration is assigned to on the Service class.
            defaults: call kwargs baked into the endpoint; a kwarg passed at
                the call site overrides the one declared here.

        Yields:
            A ``Method`` declaration, despite the annotation. ``ServiceMeta``
            turns it into a descriptor that yields a ``StreamQueryRef``.
        """
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the ServiceStreamQuery that calls this endpoint with the kwargs.

        Notes:
            - Kwargs are wrapped in a ``Dict`` child, so each value can be a Nu
              term evaluated at run rather than a fixed literal.

        Yields:
            An unevaluated interaction. Nothing is dispatched until the tree runs.
        """
        return ServiceStreamQuery(self, Dict.of(**kwargs))


class ActionRef(MethodRef):
    """Mutating scalar endpoint: calls the target for effect and for its value.

    Notes:
        - Declares the Ref slot as mutated, so the effect walk binds this Ref as
          WRITE and any narrowing or span analysis sees the endpoint as a write.
        - Nothing about the target is checked: WRITE is a declaration by the
          person writing the Service, not something read off the Python object.
        - Otherwise identical to ``QueryRef`` in dispatch: same lookup, same
          defaults merge, same sync/async rules.

    Example:
        class Calc(nu.Service):
            bump = nu.service.ActionRef.method()
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=nu.print(Calc.bump(by=3)),
        )
    """

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> ActionRef:  # type: ignore[override]
        """Declare a mutating scalar endpoint in a Service class body.

        Args:
            name: attribute to fetch on the target. Defaults to the field name
                the declaration is assigned to on the Service class.
            defaults: call kwargs baked into the endpoint; a kwarg passed at
                the call site overrides the one declared here.

        Yields:
            A ``Method`` declaration, despite the annotation. ``ServiceMeta``
            turns it into a descriptor that yields an ``ActionRef``.
        """
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the ServiceAction that calls this endpoint with the given kwargs.

        Notes:
            - Kwargs are wrapped in a ``Dict`` child, so each value can be a Nu
              term evaluated at run rather than a fixed literal.

        Yields:
            An unevaluated interaction. Nothing is dispatched until the tree runs.
        """
        return ServiceAction(self, Dict.of(**kwargs))


class StreamActionRef(MethodRef):
    """Mutating stream endpoint: calls the target for effect and for its items.

    Notes:
        - Declares the Ref slot as mutated, so the effect walk binds this Ref as
          WRITE, unlike ``StreamQueryRef``.
        - The effect is declared on the call, not on each pull, so a lazy
          generator that mutates only while being drained still reads as a write
          from the moment the call is written.
        - Same iterable / generator / async-generator bridging as
          ``StreamQueryRef``.

    Example:
        class Calc(nu.Service):
            drain = nu.service.StreamActionRef.method()
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=nu.print(nu.Collect(Calc.drain())),
        )
    """

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> StreamActionRef:  # type: ignore[override]
        """Declare a mutating stream endpoint in a Service class body.

        Args:
            name: attribute to fetch on the target. Defaults to the field name
                the declaration is assigned to on the Service class.
            defaults: call kwargs baked into the endpoint; a kwarg passed at
                the call site overrides the one declared here.

        Yields:
            A ``Method`` declaration, despite the annotation. ``ServiceMeta``
            turns it into a descriptor that yields a ``StreamActionRef``.
        """
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the ServiceStreamAction that calls this endpoint with the kwargs.

        Notes:
            - Kwargs are wrapped in a ``Dict`` child, so each value can be a Nu
              term evaluated at run rather than a fixed literal.

        Yields:
            An unevaluated interaction. Nothing is dispatched until the tree runs.
        """
        return ServiceStreamAction(self, Dict.of(**kwargs))


class CommandRef(MethodRef):
    """Mutating void endpoint: calls the target for effect and drops the value.

    Notes:
        - Declares the Ref slot as mutated, so the effect walk binds this Ref as
          WRITE.
        - Whatever the target returns is discarded, so a method that does return
          something can still be exposed here; the value is simply unreachable.
        - Use it where the call has no useful result. When you want the value,
          declare the same target attribute with ``ActionRef`` instead.

    Example:
        class Calc(nu.Service):
            reset = nu.service.CommandRef.method()
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=Calc.reset(),
        )
    """

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> CommandRef:  # type: ignore[override]
        """Declare a mutating void endpoint in a Service class body.

        Args:
            name: attribute to fetch on the target. Defaults to the field name
                the declaration is assigned to on the Service class.
            defaults: call kwargs baked into the endpoint; a kwarg passed at
                the call site overrides the one declared here.

        Yields:
            A ``Method`` declaration, despite the annotation. ``ServiceMeta``
            turns it into a descriptor that yields a ``CommandRef``.
        """
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the ServiceCommand that calls this endpoint with the given kwargs.

        Notes:
            - Kwargs are wrapped in a ``Dict`` child, so each value can be a Nu
              term evaluated at run rather than a fixed literal.

        Yields:
            An unevaluated interaction. Nothing is dispatched until the tree runs.
        """
        return ServiceCommand(self, Dict.of(**kwargs))
