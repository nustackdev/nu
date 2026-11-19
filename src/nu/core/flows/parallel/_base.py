"""Shared base for the Parallel kinds.

Owns the ``(child, "threaded"|"async")`` tuple-parsing constructor and the
class-level ``_FORCE_MODE`` slot the Threaded/Async variants override.
Compile-time laws that reject a forced-mode variant sitting over a subtree
with the wrong async-affinity fold live in ``nu.lang.laws.parallel`` -
kept there so ``nu.lang.laws`` never imports from ``nu.core.flows`` and no
cycle forms during ``nu.lang`` initialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu.lang.nu import Nu


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


__all__ = ["_ParallelBase", "checked_modes"]


_VALID_MODES = ("threaded", "async")


def _check_mode(mode: object) -> None:
    """Refuse a mode that is neither ``"threaded"`` nor ``"async"``."""
    if not isinstance(mode, str) or mode not in _VALID_MODES:
        msg = f"Parallel child mode must be 'threaded' or 'async'; got {mode!r}"
        raise ValueError(msg)


def checked_modes(modes: object, n_arms: int) -> tuple[str | None, ...]:
    """The per-arm modes a run computed: one per arm, each None or a valid mode.

    Raises:
        TypeError: the modes child did not yield a sequence.
        ValueError: a mode is not ``"threaded"`` / ``"async"`` / None, or the
            count is not one per arm.
    """
    try:
        out: tuple[str | None, ...] = tuple(cast("Iterable[str | None]", modes))
    except TypeError:
        msg = f"Parallel modes must be a sequence, got {modes!r}"
        raise TypeError(msg) from None
    if len(out) != n_arms:
        msg = f"Parallel: {len(out)} modes for {n_arms} children"
        raise ValueError(msg)
    for mode in out:
        if mode is not None:
            _check_mode(mode)
    return out


class _ParallelBase(Nu):
    """Mixin for Parallel and its forced-mode variants.

    Args:
        *items: each item is a ``Nu`` child, or a ``(child, mode)`` tuple
            pinning that one child's placement, where ``mode`` is
            ``"threaded"``, ``"async"``, or any Nu computing one of them.

    Notes:
        - Children: ``[*arms]``, or ``[*arms, modes]`` once any arm is pinned.
          ``modes`` is one child yielding a mode per arm (``None`` for an
          unpinned one), evaluated on every run, so a mode can come from a
          ref or a kv read. ``n_arms`` is the field that splits the arms from
          it; it is None, the class default, when every child is an arm.
        - A plain string mode is checked here; a computed one when it runs.
        - ``_FORCE_MODE`` is ``None`` on the smart kinds; the
          Threaded/Async subclasses set it to ``"threaded"`` / ``"async"``
          to pin every child at once, overriding per-child modes.
    """

    _FORCE_MODE: str | None = None
    n_arms: int | None = None

    def __init__(self, *items: object) -> None:
        children: list[Nu] = []
        modes: list[object] = []
        for item in items:
            if isinstance(item, tuple):
                if len(item) != 2 or not isinstance(item[0], Nu):
                    msg = (
                        f"Parallel child override must be (child, 'threaded'|'async'); got {item!r}"
                    )
                    raise TypeError(msg)
                child, mode = item
                if not isinstance(mode, Nu):
                    _check_mode(mode)
                children.append(child)
                modes.append(mode)
            elif isinstance(item, Nu):
                children.append(item)
                modes.append(None)
            else:
                msg = (
                    f"{type(self).__name__} child must be a Nu instance or "
                    f"(Nu, 'threaded'|'async') tuple; got {item!r}"
                )
                raise TypeError(msg)
        if all(mode is None for mode in modes):
            super().__init__(*children)
            return
        from nu.forms.collections.abc.sequence_interactions import TupleOf

        super().__init__(*children, cast("Callable[..., Nu]", TupleOf)(*modes))
        self.n_arms = len(children)

    def _arms(self, nids: Sequence[int]) -> Sequence[int]:
        """The arm slots of ``nids`` (this node's child nids), the modes child left out."""
        return nids if self.n_arms is None else nids[: self.n_arms]

    def _config_slots(self) -> frozenset[int]:
        """The modes child's slot, past the arms, when there is one."""
        if self.n_arms is None:
            return frozenset()
        return frozenset({self.n_arms})
