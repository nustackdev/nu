"""Eval-mode algebra in code.

The three matrices from
projects/nu/model/04-laws/02-eval-mode-algebra.md, encoded as function
bodies row by row.

The top diamond - whether the tree needs an event loop - is decided
once at the runtime entry by `tree_needs_loop`. After that, every node
inherits an `ExecState` and dispatches against its `support` set.

`Mode` here is the two-element value set `{SYNC, ASYNC}` used as elements
of `support`. NOT the legacy four-pair `(own_mode, func_mode, Mode.BOTH)`
enum that task-083 deletes.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from .nu import walk
from .span import Span
from .types import ExecState, Mode


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from .protocol import Nu


__all__ = [
    "ExecState",
    "Mode",
    "ParallelShape",
    "atom_dispatch",
    "parallel_per_child",
    "parallel_shape",
    "span_dispatch",
    "support_of",
    "tree_needs_loop",
]


class ParallelShape(Enum):
    """The three shapes a parallel node can take after per-child resolution."""

    ASYNC = "async"
    SYNC = "sync"
    HYBRID = "hybrid"


_ASYNC_ONLY = frozenset({Mode.ASYNC})
_SYNC_ONLY = frozenset({Mode.SYNC})
_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


def support_of(nu: Nu) -> frozenset[Mode]:
    """The atom's `support` set. Span recurses into its body.

    Reads the instance attribute so atoms that narrow their support at
    construction time (e.g. ``Invoke`` from an async-only callable) are
    visible to dispatch routing. Falls back to the class-level default.
    """
    if isinstance(nu, Span):
        body = nu._children[type(nu).body_slot]
        return support_of(body)
    support = getattr(nu, "support", None)
    if isinstance(support, frozenset):
        return support
    msg = f"{type(nu).__name__}: no support declared"
    raise TypeError(msg)


def tree_needs_loop(nu: Nu) -> bool:
    """The top diamond: any atom with `support == {async}` anywhere?

    Yes -> tree runs on a loop. No -> tree runs sync.
    """
    for atom in walk(nu):
        if isinstance(atom, Span):
            continue
        support = getattr(atom, "support", None)
        if support == _ASYNC_ONLY:
            return True
    return False


# --- atom dispatch matrix ---------------------------------------------------
#
# | support       | exec_state = no_loop | exec_state = loop                  |
# | {sync}        | sync impl            | sync impl (inline, last resort)    |
# | {async}       | (impossible) error   | async impl                         |
# | {sync, async} | sync impl            | async impl                         |


def atom_dispatch(atom: Nu, state: ExecState) -> Callable[[Any], Any]:
    """Pick the impl method (sync/async twin) for a Command-shaped atom.

    Producer kinds use `realization.four_method_pick` instead. For
    Commands the native pair is `run` / `arun`. The matrix decides which
    twin runs.
    """
    support = support_of(atom)
    if support == _SYNC_ONLY:
        return atom.run  # row {sync}: sync impl in both columns.
    if support == _ASYNC_ONLY:
        if state is ExecState.NO_LOOP:
            msg = (
                f"{type(atom).__name__} has support={{async}} but "
                "exec_state=no_loop. The top diamond should have forced "
                "loop. This is a runtime invariant violation."
            )
            raise RuntimeError(msg)
        return atom.arun
    if support == _BOTH:
        return atom.arun if state is ExecState.LOOP else atom.run
    msg = f"{type(atom).__name__}: invalid support {support!r}"
    raise TypeError(msg)


# --- parallel per-child dispatch matrix -------------------------------------
#
# | child subtree contains          | child's exec_state             |
# | any {async} atom                | loop (forced)                  |
# | any {sync} atom, no {async}     | no_loop (dispatch to thread)   |
# | only {sync, async} atoms        | inherit parent's exec_state    |


def parallel_per_child(child: Nu, parent_state: ExecState) -> ExecState:
    """Decide a parallel child's exec_state from its subtree contents."""
    has_async_only = False
    has_sync_only = False
    for atom in walk(child):
        if isinstance(atom, Span):
            continue
        support = getattr(atom, "support", None)
        if support == _ASYNC_ONLY:
            has_async_only = True
            break
        if support == _SYNC_ONLY:
            has_sync_only = True
    if has_async_only:
        return ExecState.LOOP
    if has_sync_only:
        return ExecState.NO_LOOP
    return parent_state


# --- parallel node shape matrix ---------------------------------------------
#
# | resolved children's exec_state | parallel shape | mechanism                |
# | all loop                        | ASYNC          | gather on the loop      |
# | all no_loop                     | SYNC           | thread pool             |
# | mixed loop and no_loop          | HYBRID         | one async queue drains  |


def parallel_shape(states: Sequence[ExecState]) -> ParallelShape:
    """Pick the parallel node shape from already-resolved child states."""
    if not states:
        return ParallelShape.SYNC
    if all(s is ExecState.LOOP for s in states):
        return ParallelShape.ASYNC
    if all(s is ExecState.NO_LOOP for s in states):
        return ParallelShape.SYNC
    return ParallelShape.HYBRID


# --- span dispatch ----------------------------------------------------------


def span_dispatch(span: Nu, state: ExecState) -> Callable[[Any], Any]:
    """Pick a Span's body method for the inherited `exec_state`.

    The Span's own `before` / `after` / policy hooks are layered around
    at the call site (runtime).
    """
    if not isinstance(span, Span):
        msg = f"span_dispatch called on non-Span: {type(span).__name__}"
        raise TypeError(msg)
    body = span._children[type(span).body_slot]
    from .realization import four_method_pick

    return four_method_pick(body, state)
