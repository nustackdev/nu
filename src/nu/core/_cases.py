"""Case labels for ``Switch`` and ``SwitchDo``: one child, run every time.

A switch holds its case labels as a child, not as a field: a label is a value
the switch compares the selector against, and a value can come from storage or
a computation (a list of labels kept in kv, a label read off a ref). The child
is a ``TupleOf`` with one item per case, so each label on its own can be a
computed term. What stays a field is the case count: it is what splits the
children into labels, branches and the default before the program runs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from nu.lang import Nu

__all__ = ["case_labels", "checked_labels"]


def case_labels(cases: Mapping[object, object]) -> Nu:
    """The labels child for ``cases``: a ``TupleOf`` of its keys, in order.

    A plain key is wrapped as a ``Literal``; a key that is a Nu term stays one
    and is computed on every run.
    """
    from nu.forms.collections_interactions import TupleOf

    return cast("Callable[..., Nu]", TupleOf)(*cases.keys())


def checked_labels(labels: object, n_cases: int, kind: str) -> tuple[object, ...]:
    """The labels a run computed, refused unless there is one per case.

    Raises:
        TypeError: the labels child did not yield an iterable.
        ValueError: it yielded more or fewer labels than there are cases.
    """
    try:
        out: tuple[object, ...] = tuple(cast("Iterable[object]", labels))
    except TypeError:
        msg = f"{kind}: the case labels must be a sequence, got {labels!r}"
        raise TypeError(msg) from None
    if len(out) != n_cases:
        msg = f"{kind}: {len(out)} case labels for {n_cases} cases"
        raise ValueError(msg)
    return out
