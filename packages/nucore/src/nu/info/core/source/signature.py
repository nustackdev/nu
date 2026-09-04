"""Signature reading: a callable in, its parameters out. No Nu knowledge.

Reports positional and keyword parameters with their defaults and
annotations, whether the callable is variadic in either direction, and
whether it is a classmethod or a staticmethod. Anything unreadable (a C
builtin, a slot wrapper) comes back as None rather than raising.
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

    def render(self, name: str) -> str:
        """A call form: ``name(a, b=default, *rest)``."""
        parts = [p.name if not p.has_default else f"{p.name}={p.default}" for p in self.positional]
        if self.variadic:
            parts.append("*children")
        parts.extend(f"{p.name}={p.default}" if p.has_default else p.name for p in self.keyword)
        return f"{name}({', '.join(parts)})"


def read_signature(target: object) -> Signature | None:
    """Read ``target``'s signature, or None when it has none to read."""
    owner = target if isinstance(target, type) else None
    func = owner.__init__ if owner is not None else target
    try:
        raw = inspect.signature(func)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    params: list[Param] = []
    variadic = keyword_variadic = False
    for index, param in enumerate(raw.parameters.values()):
        if index == 0 and owner is not None and param.name in ("self", "cls"):
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
                annotation="" if param.annotation is param.empty else _text(param.annotation),
                default="" if param.default is param.empty else _text(param.default),
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


def _text(value: object) -> str:
    """A short rendering of an annotation or default."""
    if isinstance(value, str):
        return value
    return getattr(value, "__name__", None) or repr(value)


def _is_bound_classmethod(target: object) -> bool:
    """Whether ``target`` is a classmethod, bound or unbound."""
    if isinstance(target, classmethod):
        return True
    return inspect.ismethod(target) and isinstance(getattr(target, "__self__", None), type)
