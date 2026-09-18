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

from nu.inspect.core.contract import (
    YIELDS,
    Arg,
    Violation,
    call_form,
    check_args,
    check_example,
    check_summary,
    render_args,
)
from nu.inspect.core.docstring import split_docstring
from nu.inspect.core.source import public_members, read_signature, unpacked_count
from nu.inspect.record import Record, prose
from nu.inspect.taxonomy import taxonomy
from nu.lang import Form
from nu.lang.kinds import Interaction, Ref


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
    and from the docstring when it inherits the variadic ``Nu.__init__``;
    ``call`` is the same arguments spelled the way a person writes them.
    ``kind``, ``sort``, ``cardinality`` and ``abstract`` are taxonomy facts
    read off ``nu.lang.kinds``.
    """

    args: tuple[Arg, ...] = ()
    call: str = ""
    yields: str = ""
    kind: str = ""
    sort: str = ""
    cardinality: str = ""
    abstract: bool = False

    @property
    def arity(self) -> int | None:
        """The exact child count, or None when it is not known."""
        if not self.args or any(arg.variadic for arg in self.args):
            return None
        return len(self.args)

    @property
    def required(self) -> int:
        """How many children carry no default."""
        return sum(1 for arg in self.args if not arg.variadic and not arg.has_default)


def parse_interaction(
    atom: type, path: str = "", *, aliases: tuple[str, ...] = ()
) -> InteractionRecord:
    """One InteractionRecord for ``atom``."""
    blocks = split_docstring(atom.__doc__)
    args = call_form(atom, blocks)
    return InteractionRecord(
        **prose(
            atom,
            atom.__name__,
            path or f"{atom.__module__}.{atom.__name__}",
            blocks,
            aliases=aliases,
        ),
        **taxonomy(atom),
        args=args,
        call=render_args(atom.__name__, args),
        yields=blocks.text_of(*YIELDS),
    )


def catalogue(module: ModuleType) -> tuple[InteractionRecord, ...]:
    """A record per interaction the module exports, in export order.

    Forms and Refs are excluded. Both are Interaction subclasses by
    inheritance, so a naive check reports every Form twice - once here and
    once in the Form catalogue - and the three catalogues stop partitioning
    the module. Same most-specific-wins dispatch ``Inspect`` uses on a single
    class.
    """
    name = module.__name__
    return tuple(
        parse_interaction(member.target, path=f"{name}.{member.name}", aliases=member.aliases)
        for member in public_members(module)
        if isinstance(member.target, type) and _is_interaction(member.target)
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


def _is_interaction(cls: type) -> bool:
    if not issubclass(cls, Interaction):
        return False
    return not issubclass(cls, Form) and not issubclass(cls, Ref)
