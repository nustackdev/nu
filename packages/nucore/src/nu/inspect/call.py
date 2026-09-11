"""The call kind: record, parse, verify.

A call is a callable a person or a model writes to build Nu: a bound method
like ``.set(v)``, an operator like ``a + b``, a classmethod like
``List.of(x, y)``, or a free function like ``nu.str(x)``. What differs across
them is the syntax and where it is bound; the described thing is the same.

Signature and return annotation are authoritative for args and yields, so
neither is written; the docstring's job is summary and notes.

A call is reached two ways: off a class, by the MRO walk the builder kinds
run, or off a module, by the catalogue here - which is what the ``nu.std``
surfaces are made of.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.inspect.core.contract import YIELDS, Arg, Violation, call_form, check_summary, render_args
from nu.inspect.core.docstring import split_docstring
from nu.inspect.core.source import public_members
from nu.inspect.record import Record, prose


if TYPE_CHECKING:
    from types import ModuleType

    from nu.inspect.core.source import Binding


__all__ = [
    "CallRecord",
    "call_for",
    "catalogue",
    "parse_binding",
    "parse_call",
    "spelling_for",
    "verify_call",
]


@dataclass(frozen=True)
class CallRecord(Record):
    """One callable subject: what to write, and what it takes and yields.

    ``spelling`` is the surface form with its arguments elided: ``.set(...)``
    for a method, ``a + b`` for an operator, ``math.sqrt(...)`` for a free
    function. ``call`` is the same form with the real argument list in it,
    ``.inc(step=1)``, so a reader who needs the arity does not reassemble it.

    ``args`` merges the signature (names, defaults, annotations) with the
    docstring's Args prose, with the receiver of a method dropped: ``self`` is
    what you call the method on, not something you write. ``returns`` is the
    return annotation as text; ``yields`` is the docstring's Yields prose,
    which carries meaning the annotation cannot - sentinel behaviour,
    promotion rules, edge conditions. Both belong; one is the type, the other
    is the semantics.
    """

    spelling: str = ""
    call: str = ""
    args: tuple[Arg, ...] = ()
    yields: str = ""
    returns: str = ""
    owner: str = ""
    binding: str = ""  # "method" | "classmethod" | "operator" | "function"


_SPELLINGS: dict[str, str] = {
    "__add__": "a + b",
    "__sub__": "a - b",
    "__mul__": "a * b",
    "__truediv__": "a / b",
    "__floordiv__": "a // b",
    "__mod__": "a % b",
    "__pow__": "a ** b",
    "__matmul__": "a @ b",
    "__neg__": "-a",
    "__pos__": "+a",
    "__abs__": "abs(a)",
    "__invert__": "~a",
    "__lshift__": "a << b",
    "__rshift__": "a >> b",
    "__and__": "a & b",
    "__or__": "a | b",
    "__xor__": "a ^ b",
    "__gt__": "a > b",
    "__lt__": "a < b",
    "__ge__": "a >= b",
    "__le__": "a <= b",
    "__eq__": "a == b",
    "__ne__": "a != b",
    "__getitem__": "a[key]",
    "__setitem__": "a[key] = value",
    "__contains__": "value in a",
    "__len__": "len(a)",
    "__iter__": "iter(a)",
    "__call__": "a(...)",
}


def spelling_for(name: str, binding: str, qualifier: str = "") -> str:
    """The surface form for ``name``, given its binding."""
    if binding == "operator":
        return _SPELLINGS.get(name, name)
    if binding in ("classmethod", "function"):
        return f"{qualifier}.{name}(...)" if qualifier else f"{name}(...)"
    return f".{name}(...)"


def call_for(name: str, binding: str, args: tuple[Arg, ...], qualifier: str = "") -> str:
    """The surface form for ``name``, with its arguments written out."""
    if binding == "operator":
        return _SPELLINGS.get(name, name)
    rendered = render_args(name, args)
    if binding in ("classmethod", "function"):
        return f"{qualifier}.{rendered}" if qualifier else rendered
    return f".{rendered}"


def parse_call(
    target: object,
    *,
    name: str,
    path: str,
    owner: str,
    binding: str,
    qualifier: str = "",
    aliases: tuple[str, ...] = (),
) -> CallRecord:
    """One CallRecord for ``target``, however it was reached."""
    blocks = split_docstring(getattr(target, "__doc__", ""))
    args = call_form(target, blocks, receiver=binding in ("method", "operator"))
    return CallRecord(
        **prose(target, name, path, blocks, aliases=aliases),
        spelling=spelling_for(name, binding, qualifier),
        call=call_for(name, binding, args, qualifier),
        args=args,
        yields=blocks.text_of(*YIELDS),
        returns=_return_annotation(target),
        owner=owner,
        binding=binding,
    )


def parse_binding(binding: Binding, *, host: type) -> CallRecord:
    """A CallRecord for a member reached by an MRO walk on ``host``."""
    kind = _binding_kind(binding.name, binding.raw)
    defining = binding.defining
    owner = f"{defining.__module__}.{defining.__qualname__}"
    qualifier = host.__name__ if kind == "classmethod" else ""
    path = f"{host.__module__}.{host.__qualname__}.{binding.name}"
    return parse_call(
        binding.target,
        name=binding.name,
        path=path,
        owner=owner,
        binding=kind,
        qualifier=qualifier,
    )


def catalogue(module: ModuleType) -> tuple[CallRecord, ...]:
    """A CallRecord per free function the module exports, in export order.

    The other catalogues filter a module for a kind of class. This one is for
    the surfaces that export no classes at all: ``nu.std.math`` is 34 plain
    functions that build Nu terms, and without this every std submodule reads
    as exporting nothing.

    The qualifier is the module's last name part, because that is how the
    function is written: ``from nu.std import math``, then ``math.sqrt(x)``.
    """
    name = module.__name__
    qualifier = name.rsplit(".", 1)[-1]
    return tuple(
        parse_call(
            member.target,
            name=member.name,
            path=f"{name}.{member.name}",
            owner=getattr(member.target, "__module__", ""),
            binding="function",
            qualifier=qualifier,
            aliases=member.aliases,
        )
        for member in public_members(module)
        if _is_free_function(member.target)
    )


def verify_call(target: object, *, subject: str = "") -> list[Violation]:
    """Every way ``target``'s docstring lies about the format."""
    name = subject or getattr(target, "__name__", repr(target))
    blocks = split_docstring(getattr(target, "__doc__", ""))
    return check_summary(name, blocks)


def _is_free_function(target: object) -> bool:
    """Whether a module member is a function rather than one of the class kinds."""
    return callable(target) and not isinstance(target, type)


def _binding_kind(name: str, raw: object) -> str:
    if isinstance(raw, classmethod):
        return "classmethod"
    if name.startswith("__") and name.endswith("__"):
        return "operator"
    return "method"


def _return_annotation(target: object) -> str:
    func = target
    if isinstance(target, (classmethod, staticmethod)):
        func = target.__func__
    try:
        raw = inspect.signature(func)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return ""
    if raw.return_annotation is inspect.Signature.empty:
        return ""
    ann = raw.return_annotation
    if isinstance(ann, str):
        return ann
    return getattr(ann, "__name__", None) or repr(ann)
