"""Check an interaction atom against the guide.

Composes the contract's shared checks and adds the two things only an
interaction knows: that a Command writes rather than yields, and how many
children the code really takes when the constructor will not say.
"""

from __future__ import annotations

from nu.info.core.contract import (
    Problem,
    check_args,
    check_example,
    check_summary,
    check_yields,
)
from nu.info.core.docstring import split_docstring
from nu.info.core.source import read_signature, unpacked_count
from nu.lang.kinds import Command


__all__ = [
    "unpacked_arity",
    "validate_interaction",
]


def validate_interaction(atom: type) -> list[Problem]:
    """Every way ``atom``'s docstring diverges from the guide."""
    name = atom.__name__
    blocks = split_docstring(atom.__doc__)
    summary = check_summary(name, blocks)
    if not blocks.summary:
        return summary

    problems = [*summary, *check_args(name, blocks, _expected_arity(atom))]
    if not issubclass(atom, Command):
        problems.extend(check_yields(name, blocks))
    problems.extend(check_example(name, blocks))
    return problems


def unpacked_arity(atom: type) -> int | None:
    """The child count ``_compile`` unpacks, or None when it does not unpack.

    Declaration is the data and derivation is the checker: Args says how many
    children an atom takes, and this is how that claim is held to the code.
    Reads source, so it is never called while building a record.

    Args:
        atom: the interaction class to read.

    Returns:
        The number of names the thunk unpacks ``children`` into. None when the
        atom declares no ``_compile``, when the source cannot be read, or when
        it folds its children rather than unpacking them, as ``Add`` does.
    """
    compile_fn = atom.__dict__.get("_compile")
    if compile_fn is None:
        return None
    return unpacked_count(compile_fn, "children")


def _expected_arity(atom: type) -> int | None:
    """How many children the code says the atom takes, or None if unreadable.

    The declared constructor when there is one, otherwise what ``_compile``
    unpacks. A variadic constructor with no unpacking reads as None: it really
    could be any number, and the docstring is the only authority.
    """
    signature = read_signature(atom)
    if signature is not None and signature.params:
        return None if signature.variadic else len(signature.positional)
    return unpacked_arity(atom)
