"""The call kind: record, parse, verify.

A call is a callable a person or a model writes to build Nu: a bound method
like ``.set(v)``, an operator like ``a + b``, a classmethod like
``List.of(x, y)``, or a free function like ``nu.str(x)``. What differs across
them is the syntax and where it is bound; the described thing is the same.

Signature and return annotation are authoritative for args and yields, so
neither is written; the docstring's job is summary and notes.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.inspect.core.contract import YIELDS, Arg, Violation, call_form, check_summary
from nu.inspect.core.docstring import split_docstring
from nu.inspect.record import Record, prose


if TYPE_CHECKING:
    from nu.inspect.core.source import Binding


__all__ = [
    "CallRecord",
    "parse_binding",
    "parse_call",
    "spelling_for",
    "verify_call",
]


@dataclass(frozen=True)
class CallRecord(Record):
    """One callable subject: what to write, and what it takes and yields.

    ``spelling`` is the surface form: ``.set(value)`` for a method, ``a + b``
    for an operator, ``nu.str(x)`` for a free function.

    ``args`` merges the signature (names, defaults) with the docstring's Args
    prose. ``returns`` is the return annotation as text; ``yields`` is the
    docstring's Yields prose, which carries meaning the annotation cannot -
    sentinel behaviour, promotion rules, edge conditions. Both belong; one
    is the type, the other is the semantics.
    """

    spelling: str = ""
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


def parse_call(
    target: object,
    *,
    name: str,
    path: str,
    owner: str,
    binding: str,
    qualifier: str = "",
) -> CallRecord:
    """One CallRecord for ``target``, however it was reached."""
    blocks = split_docstring(getattr(target, "__doc__", ""))
    return CallRecord(
        **prose(target, name, path, blocks),
        spelling=spelling_for(name, binding, qualifier),
        args=call_form(target, blocks),
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


def verify_call(target: object, *, subject: str = "") -> list[Violation]:
    """Every way ``target``'s docstring lies about the format."""
    name = subject or getattr(target, "__name__", repr(target))
    blocks = split_docstring(getattr(target, "__doc__", ""))
    return check_summary(name, blocks)


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
