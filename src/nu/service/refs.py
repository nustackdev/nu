"""Service MethodRefs: one Ref class per canonical Nu kind.

QueryRef         (ScalarQuery)   — pure scalar read.
StreamQueryRef   (StreamQuery)   — pure stream read.
ActionRef        (ScalarAction)  — mutating scalar call, yields a value.
StreamActionRef  (StreamAction)  — mutating stream call, yields items.
CommandRef       (Command)       — mutating void call, yields nothing.

`.method(name=...)` names the attribute on the target object; if omitted,
the descriptor's field name on the Service class is used.
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
    """Read-only scalar endpoint on a Python target."""

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> QueryRef:  # type: ignore[override]
        """Package this Ref class + config as a Method declaration."""
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct the matching Service interaction over the given kwargs."""
        return ServiceQuery(self, Dict.of(**kwargs))


class StreamQueryRef(MethodRef):
    """Read-only stream endpoint on a Python target."""

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> StreamQueryRef:  # type: ignore[override]
        """Package this Ref class + config as a Method declaration."""
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct the matching Service interaction over the given kwargs."""
        return ServiceStreamQuery(self, Dict.of(**kwargs))


class ActionRef(MethodRef):
    """Mutating scalar endpoint on a Python target."""

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> ActionRef:  # type: ignore[override]
        """Package this Ref class + config as a Method declaration."""
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct the matching Service interaction over the given kwargs."""
        return ServiceAction(self, Dict.of(**kwargs))


class StreamActionRef(MethodRef):
    """Mutating stream endpoint on a Python target."""

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> StreamActionRef:  # type: ignore[override]
        """Package this Ref class + config as a Method declaration."""
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct the matching Service interaction over the given kwargs."""
        return ServiceStreamAction(self, Dict.of(**kwargs))


class CommandRef(MethodRef):
    """Mutating void endpoint on a Python target: yields nothing."""

    @classmethod
    def method(cls, name: str | None = None, **defaults: object) -> CommandRef:  # type: ignore[override]
        """Package this Ref class + config as a Method declaration."""
        return Method(cls, target_attr=name, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct the matching Service interaction over the given kwargs."""
        return ServiceCommand(self, Dict.of(**kwargs))
