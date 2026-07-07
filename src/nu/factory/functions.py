"""``ScalarQueryFactory``: kind-fixed function factory.

Trivial wrapper around ``InteractionFactory`` that fixes the base to
``ScalarQuery`` - the easiest argument to get wrong when the caller wants
"turn this pure Python function into a read atom." Sibling helpers
(``CommandFactory`` etc.) can be added the same way when a consumer needs
them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang.kinds import ScalarQuery

from .core import InteractionFactory


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ["ScalarQueryFactory"]


def ScalarQueryFactory(  # noqa: N802 -- a class factory; reads as a class at the call site
    name: str,
    fn: Callable[..., object],
    *,
    propagate_sentinels: bool = True,
    **attributes: object,
) -> type[ScalarQuery]:
    """Build a ``ScalarQuery`` atom from a callable - the common-case helper.

    Equivalent to ``InteractionFactory(ScalarQuery, name, fn, ...)``; fixes
    the base kind, which is the easiest argument to get wrong.
    """
    return InteractionFactory(
        ScalarQuery, name, fn, propagate_sentinels=propagate_sentinels, **attributes
    )
