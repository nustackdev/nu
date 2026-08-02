"""``@host``: decorator sugar over ``InteractionFactory``.

Turns a host Python callable into a Nu atom with minimal ceremony. Default
base is ``ScalarQuery``; atom name defaults to the function's ``__name__``
snake-cased into CamelCase.

    @nu.host
    def creation_mint(tx) -> str: ...

    @nu.host(deterministic=False)
    def now() -> float: ...

    @nu.host(base=Command)
    def dispatch(x, y) -> None: ...

Also usable as a plain wrapper on an existing callable::

    MintFromTx = nu.host(extract_mint)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang.kinds import ScalarQuery

from .core import InteractionFactory


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.nu import Nu


__all__ = ["host"]


def _snake_to_camel(snake: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in snake.lstrip("_").split("_"))


def host(  # type: ignore[misc]
    fn: Callable[..., object] | None = None,
    *,
    name: str | None = None,
    base: type[Nu] | None = None,
    propagate_sentinels: bool = True,
    **attributes: object,
) -> object:
    """Decorator sugar over ``InteractionFactory``: turn a host callable into a Nu atom.

    Default base is ``ScalarQuery``; atom name defaults to the function's
    ``__name__`` snake-cased into CamelCase.
    """

    def wrap(f: Callable[..., object]) -> type[Nu]:
        atom_name = name or _snake_to_camel(getattr(f, "__name__", "Host"))
        atom_base = base or ScalarQuery
        return InteractionFactory(
            atom_base,
            atom_name,
            f,
            propagate_sentinels=propagate_sentinels,
            **attributes,
        )

    if fn is None:
        return wrap
    return wrap(fn)
