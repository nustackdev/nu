"""The interaction kind: record, parse, verify.

An interaction is an atom: an ``nu.lang.kinds.Interaction`` subclass. It is a
node in the tree, with children and a kind/sort/cardinality declared on the
class. Its args come from the docstring when the constructor is variadic;
its yields come from the docstring (there is no return annotation on
``_compile``). What the code says is derived here; what the docstring says is
read; the two are checked against each other by the shared laws.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.info.core.contract import (
    YIELDS,
    Arg,
    Violation,
    call_form,
    check_args,
    check_example,
    check_summary,
)
from nu.info.core.docstring import split_docstring
from nu.info.core.source import public_members, read_signature, unpacked_count
from nu.info.record import Record, prose
from nu.lang import kinds
from nu.lang.kinds import Interaction


if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    "InteractionRecord",
    "catalogue",
    "parse_interaction",
    "unpacked_arity",
    "verify_interaction",
]


@dataclass(frozen=True)
class InteractionRecord(Record):
    """One atom: the prose, plus what the code says it is.

    ``args`` is the call form, from the constructor when the atom declares one
    and from the docstring when it inherits the variadic ``Nu.__init__``.
    ``kind``, ``sort`` and ``cardinality`` are taxonomy facts read off
    ``nu.lang.kinds``.
    """

    args: tuple[Arg, ...] = ()
    yields: str = ""
    kind: str = ""
    sort: str = ""
    cardinality: str = ""

    @property
    def arity(self) -> int | None:
        """The exact child count, or None when it is not known."""
        if not self.args or any(arg.variadic for arg in self.args):
            return None
        return len(self.args)

    @property
    def required(self) -> int:
        """How many children carry no default."""
        return sum(1 for arg in self.args if not arg.variadic and not arg.default)


_KIND_CLASSES = tuple(
    getattr(kinds, name) for name in kinds.__all__ if isinstance(getattr(kinds, name), type)
)


def parse_interaction(atom: type, path: str = "") -> InteractionRecord:
    """One InteractionRecord for ``atom``."""
    blocks = split_docstring(atom.__doc__)
    return InteractionRecord(
        **prose(atom, atom.__name__, path or f"{atom.__module__}.{atom.__name__}", blocks),
        args=call_form(atom, blocks),
        yields=blocks.text_of(*YIELDS),
        kind=_kind(atom),
        sort=_declared(atom, "sort"),
        cardinality=_declared(atom, "cardinality"),
    )


def catalogue(module: ModuleType) -> tuple[InteractionRecord, ...]:
    """A record per interaction the module exports, in export order."""
    name = module.__name__
    return tuple(
        parse_interaction(member.target, path=f"{name}.{member.name}")
        for member in public_members(module)
        if isinstance(member.target, type) and issubclass(member.target, Interaction)
    )


def verify_interaction(atom: type) -> list[Violation]:
    """Every way ``atom``'s docstring lies about the code."""
    name = atom.__name__
    blocks = split_docstring(atom.__doc__)
    violations = check_summary(name, blocks)
    violations.extend(check_args(name, blocks, _expected_arity(atom)))
    violations.extend(check_example(name, blocks))
    return violations


def unpacked_arity(atom: type) -> int | None:
    """The child count ``_compile`` unpacks, or None when it does not unpack."""
    compile_fn = atom.__dict__.get("_compile")
    if compile_fn is None:
        return None
    return unpacked_count(compile_fn, "children")


def _expected_arity(atom: type) -> int | None:
    """How many children the code says the atom takes, or None if unreadable."""
    signature = read_signature(atom)
    if signature is not None and signature.params:
        return None if signature.variadic else len(signature.positional)
    return unpacked_arity(atom)


def _kind(atom: type) -> str:
    for base in atom.__mro__:
        if base in _KIND_CLASSES:
            return base.__name__
    return ""


def _declared(atom: type, name: str) -> str:
    attribute = getattr(atom, "_attributes", {}).get(name)
    if attribute is None:
        return ""
    value = getattr(attribute, "value", None)
    return getattr(value, "value", None) or str(value)
