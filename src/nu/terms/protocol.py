"""Protocol surface for Nu kinds.

The minimum each Nu must satisfy. Each member here is load-bearing for
one algebra module. Algebra modules type-hint these protocols, not the
concrete kind classes - this is what lets new dialect kinds plug in
without subclassing `NuBase`.

See task-083 architecture.md for the load-bearing table.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    Protocol,
    runtime_checkable,
)


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Iterator, Mapping

    from .types import Effect, Mode, Realization


__all__ = [
    "AlgebraAtom",
    "CommandAtom",
    "EffectAtom",
    "EvalAtom",
    "Nu",
    "ScalarProducer",
    "StreamProducer",
    "Transparent",
]


@runtime_checkable
class Nu(Protocol):
    """The root protocol.

    Every Nu is a tree of children plus the composition operators.
    """

    _children: tuple[Nu, ...]

    def _with_children(self, children: tuple[Nu, ...]) -> Nu: ...
    def __rshift__(self, other: Nu) -> Nu: ...
    def __or__(self, other: Nu) -> Nu: ...


class EffectAtom(Nu, Protocol):
    """A Nu that declares class-time effect annotations.

    `own_effects` keys are slot indices; values are a single Effect or a
    frozenset for slots that genuinely carry multiple directions
    (read-modify-write atomic).
    """

    own_effects: ClassVar[Mapping[int, Effect | frozenset[Effect]]]


class AlgebraAtom(Nu, Protocol):
    """A Nu that declares its algebraic flags."""

    commutative: ClassVar[bool | Literal["if-independent"]]
    associative: ClassVar[bool]
    idempotent: ClassVar[bool]
    deterministic: ClassVar[bool]


class EvalAtom(Nu, Protocol):
    """A Nu that participates in eval-mode dispatch."""

    support: ClassVar[frozenset[Mode]]


class ScalarProducer(EvalAtom, Protocol):
    """Native-scalar producer - produces a single value."""

    realization: ClassVar[Realization]

    def eval(self, ctx: Any) -> Any: ...  # noqa: ANN401, D102
    def aeval(self, ctx: Any) -> Awaitable[Any]: ...  # noqa: ANN401, D102


class StreamProducer(EvalAtom, Protocol):
    """Native-stream producer - produces N values."""

    realization: ClassVar[Realization]

    def open(self, ctx: Any) -> Iterator[Any]: ...  # noqa: ANN401, D102
    def aopen(self, ctx: Any) -> AsyncIterator[Any]: ...  # noqa: ANN401, D102


class CommandAtom(EvalAtom, Protocol):
    """Effect-bearing Nu that yields nothing."""

    def run(self, ctx: Any) -> None: ...  # noqa: ANN401, D102
    def arun(self, ctx: Any) -> Awaitable[None]: ...  # noqa: ANN401, D102


class Transparent(Nu, Protocol):
    """Span-shaped Nu - role and realization inherited from `body_slot`."""

    body_slot: ClassVar[int]
