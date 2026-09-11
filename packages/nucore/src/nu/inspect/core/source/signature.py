"""Signature reading: a callable in, its parameters out. No Nu knowledge.

Reports positional and keyword parameters with their defaults and
annotations, whether the callable is variadic in either direction, and
whether it is a classmethod or a staticmethod. Anything unreadable (a C
builtin, a slot wrapper) comes back as None rather than raising.

Rendering a call form is not here: it is built from the merged arguments, so
it belongs to ``core.contract.call`` where the merge happens.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass


__all__ = [
    "Param",
    "Signature",
    "read_signature",
]

_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


@dataclass(frozen=True)
class Param:
    """One parameter of a callable."""

    name: str
    keyword_only: bool = False
    annotation: str = ""
    default: str = ""
    has_default: bool = False


@dataclass(frozen=True)
class Signature:
    """A callable's parameters, flattened."""

    params: tuple[Param, ...] = ()
    variadic: bool = False
    keyword_variadic: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False

    @property
    def positional(self) -> tuple[Param, ...]:
        """Parameters callable by position."""
        return tuple(p for p in self.params if not p.keyword_only)

    @property
    def keyword(self) -> tuple[Param, ...]:
        """Keyword-only parameters."""
        return tuple(p for p in self.params if p.keyword_only)

    @property
    def required(self) -> int:
        """How many positional parameters carry no default."""
        return sum(1 for p in self.positional if not p.has_default)


def read_signature(target: object, *, receiver: bool = False) -> Signature | None:
    """Read ``target``'s signature, or None when it has none to read.

    Args:
        target: the callable, or a class whose ``__init__`` is read.
        receiver: whether ``target`` is an unbound method, whose leading
            ``self`` or ``cls`` is the receiver rather than a parameter. A
            class knows this about its own ``__init__``; a function reached by
            an MRO walk does not, and only the caller that walked it can say.

    Returns:
        The parameters, or None when the callable is unreadable.
    """
    owner = target if isinstance(target, type) else None
    func = owner.__init__ if owner is not None else target
    try:
        raw = inspect.signature(func)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    params: list[Param] = []
    variadic = keyword_variadic = False
    for index, param in enumerate(raw.parameters.values()):
        if index == 0 and (owner is not None or receiver) and param.name in ("self", "cls"):
            continue
        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            variadic = True
            continue
        if param.kind is inspect.Parameter.VAR_KEYWORD:
            keyword_variadic = True
            continue
        params.append(
            Param(
                name=param.name,
                keyword_only=param.kind not in _POSITIONAL,
                annotation=(
                    "" if param.annotation is param.empty else _annotation_text(param.annotation)
                ),
                default="" if param.default is param.empty else _default_text(param.default),
                has_default=param.default is not param.empty,
            )
        )
    return Signature(
        params=tuple(params),
        variadic=variadic,
        keyword_variadic=keyword_variadic,
        is_classmethod=_is_bound_classmethod(target),
        is_staticmethod=isinstance(target, staticmethod),
    )


def _annotation_text(value: object) -> str:
    """A short rendering of an annotation.

    An annotation names a type, so a string annotation is already its own
    name (``def f(x: "Int")``) and a class renders as its bare name.
    """
    if isinstance(value, str):
        return value
    return getattr(value, "__name__", None) or repr(value)


def _default_text(value: object) -> str:
    """A short rendering of a default value.

    A default is a value, not a name, so it renders as source a caller could
    paste back: ``'item'``, ``' '``, a newline literal, ``False``, ``1``, ``None``. A
    class used as a default keeps its bare name, since ``<class 'x.Y'>`` is
    not source either.
    """
    if isinstance(value, type):
        return value.__name__
    return repr(value)


def _is_bound_classmethod(target: object) -> bool:
    """Whether ``target`` is a classmethod, bound or unbound."""
    if isinstance(target, classmethod):
        return True
    return inspect.ismethod(target) and isinstance(getattr(target, "__self__", None), type)
