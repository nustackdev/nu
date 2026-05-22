"""The Term primitive and its metaclass.

A Term is layer 0's node: a kind (its class), an ordered tuple of child
Symbols, and an opaque payload. It is pure immutable data with no parent and
no position. The metaclass collects Attribute declarations off the class body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure.attribute import Attribute


if TYPE_CHECKING:
    from typing import ClassVar, Self

__all__ = ["Term", "TermMeta"]


class TermMeta(type):
    """Metaclass that collects Attribute declarations off a Term class body."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
    ) -> TermMeta:
        """Build the class and attach the attributes collected across its MRO."""
        cls = super().__new__(mcs, name, bases, namespace)
        attributes: dict[str, Attribute] = {}
        for klass in reversed(cls.__mro__):
            for key, value in vars(klass).items():
                if isinstance(value, Attribute):
                    if value.name is None:
                        value.name = key
                    attributes[value.name] = value
        cls._attributes = attributes
        return cls


class Term(metaclass=TermMeta):
    """Pure immutable construction data: a kind, children, and a payload.

    A description is a DAG of Symbols. Constructing one builds a nested
    immutable value and nothing else: no store, no evaluation, no checks.
    """

    _attributes: ClassVar[dict[str, Attribute]]

    def __init__(self, *children: Term) -> None:
        self.children: tuple[Term, ...] = children
        self.payload: dict[str, object] = {}

    def with_children(self, *children: Term) -> Self:
        """Return a variant of this Term with different children.

        The original is untouched; the variant shares the same payload.
        """
        variant = object.__new__(type(self))
        variant.children = children
        variant.payload = self.payload
        return variant

    def __repr__(self) -> str:
        if "name" in self.payload:
            return str(self.payload["name"])
        if "value" in self.payload:
            return repr(self.payload["value"])
        if not self.children:
            return type(self).__name__
        inner = ", ".join(repr(child) for child in self.children)
        return f"{type(self).__name__}({inner})"
