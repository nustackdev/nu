"""Assembled lenses: the whole surface as one tree, ready to run.

The rest of this package is deliberately fabric-free. :mod:`.columns` builds a
term and :mod:`.ref` sends frames, and neither needs a store to do its job, so
neither imports one -- that is what lets them compose into something other than
a browser (a test, a report, a different host) without dragging kv along.

Running that term is a different job, and it does need a store, because reads
have to happen inside a storage boundary and a term built at run time is
invisible to the pass that would otherwise place one. Somebody has to write the
``Snapshot``. Leaving it to the caller makes it a contract they have to know
and can silently get wrong; doing it here costs this one module an import of
:mod:`nustd.kv`.

So the layering is: primitives know nothing about fabrics, the preset knows
about kv. Reach for :func:`browse` when you want a working lens. Reach past it,
for :func:`~nustd.ui.lens.columns.columns` and the Ref, when you want the
cascade somewhere else, on your own boundary, or driven by something that is
not a browser cursor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
import nustd.kv

from .columns import DEFAULT_MAX_ROWS, columns


if TYPE_CHECKING:
    from nu.domains.shape import Shape
    from nu.domains.shape.refs import StructuredRef

    from .ref import LensRef


__all__ = ["browse"]


def _nav_key(lens: LensRef) -> str:
    """Where this arm parks the cursor the browser sent.

    Derived from the lens's own slot chain rather than taken as an argument.
    It is pure mechanism -- an attrs side-channel between the subscription and
    the body one line below it -- so a caller has no reason to name it, and a
    default they could forget to override is a collision waiting to happen:
    two arms binding one key in a composition read each other's cursor. Two
    lenses are two chains, so two keys, and the name says which lens in a
    trace.
    """
    segments: list[str] = []
    ref: StructuredRef | None = lens
    while ref is not None:
        segments.append(str(ref._payload.get("segment", "")))
        ref = ref._parent
    segments.reverse()
    return f"_lens_nav.{'.'.join(segments)}"


def browse(
    lens: LensRef,
    shape: type[Shape],
    *,
    prefix: StructuredRef | None = None,
    max_rows: int = DEFAULT_MAX_ROWS,
) -> nu.Nu:
    """A working lens, as one tree: the first cascade, then one per move.

    Argument for argument this is :func:`~nustd.ui.lens.columns.columns` with
    the lens in front and the cursor taken out. The cursor is the one thing a
    caller cannot supply, because it does not exist yet -- it is whatever the
    browser sends, and the arm below is what turns each one into a cascade.

    The first cascade is built here rather than waited for: the empty cursor is
    the one cursor that is known before the browser says anything, so the page
    paints on the first frame instead of on the first click.

    Never finishes, which is what the ws host holds a tab's program to. Put
    several in a :class:`nu.ParallelAsync` -- not in a smart ``|``, which
    refuses to pick a mode for a branch whose term appears at run time.

    Args:
        lens: the ``LensRef`` on the mounted page, already reachable through
            its slot chain so its wire path resolves.
        shape: what to expect, and what the browser's cursor is relative to.
        prefix: where ``shape`` lives. None reads it at the root of its own
            store. Never sent to the browser, so a lens given one cannot be
            navigated above it.
        max_rows: the per-column cap. Pass the same number the slot declared,
            or the browser's ``n/total`` note disagrees with what was clipped.

    Example:
        ui = nu.ParallelAsync(
            browse(App.home.all.lens, Cluster),
            browse(App.home.one.lens, Machine, prefix=Cluster.machines["red"]),
        )
    """
    key = _nav_key(lens)
    boot = nustd.kv.Snapshot(
        lens.set_columns(
            nu.List.of(),
            columns(shape, nu.List.of(), prefix=prefix, max_rows=max_rows),
        )
    )
    # Two reads of one key, built separately: a Nu node is a value, and one
    # object sitting in two tree positions is one compiled node that the two
    # of them would then share at run time.
    moved = nu.ReactForever(
        lens.on_nav(),
        nustd.kv.Snapshot(
            lens.set_columns(
                nu.ListAttrRef(key),
                columns(shape, nu.ListAttrRef(key), prefix=prefix, max_rows=max_rows),
            )
        ),
        changed_key=key,
    )
    return boot >> moved
