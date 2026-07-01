"""Annotation rewrites -- logging and step-tracking transforms over a Nu tree.

Structural rewrites (built on ``nu.tree``) that layer observability onto a tree
without touching its result:

- ``annotate_steps``   - wrap each child of a ``Sequential`` in a step-tracking
                         Bracket that logs ``start`` / ``done`` / ``failed``.
- ``annotate_retries`` - log every *failed attempt* of a ``Retry`` (async path
                         only - the sync ``Retry`` runs no hooks). Final
                         exhaustion is deliberately NOT logged, so the terminal
                         error still propagates unswallowed (see below).
- ``set_logger_name``  - retarget the logger on every step span and log node.

All logging goes through the stderr side of the stdio fabric (``nu.core.io``),
so a bound ``StdioBackend`` captures it in a test exactly like ``print`` output.
The step Bracket logs imperatively in its ``scope`` (it wraps a body, so it
cannot delegate to a ``LogCommand`` child); the retry hooks are real
``LogCommand`` nodes that read the attempt / error the ``Retry`` writes into
``ctx.attrs``.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, cast

from nu.context import IntAttrRef, StrAttrRef
from nu.core import LiteralQuery, Noop
from nu.core.io import LogCommand, _emit_log, log
from nu.flows import Sequential
from nu.spans.bracket import _LifecycleBracket
from nu.spans.policy import Retry
from nu.tree import map_nodes


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.lang import Command, Flow, Nu, Span
    from nu.lang.runtime import Context

    Hook = Flow | Command | Span


__all__ = [
    "annotate_retries",
    "annotate_steps",
    "set_logger_name",
]

_STEP_LOGGER = "nu.steps"
_RETRY_LOGGER = "nu.retry"
_RETRY_ARITY = 10  # Retry's fixed child count (nu.spans.policy.Retry)


# --- the step-tracking Bracket ----------------------------------------------


class _StepSpan(_LifecycleBracket):
    """Wraps one sequential step to log its progress. Metadata rides in payload.

    A transparent Bracket (body at slot 0): it forwards the body's yield and
    only logs around it. Its ``step`` / ``total`` / ``path`` / ``logger`` are
    construction constants (not per-run state), so they live in ``payload`` -
    which ``with_children`` carries across a rewrite untouched.
    """

    def __init__(self, child: Nu, step: int, total: int, path: str, logger: str = _STEP_LOGGER) -> None:
        super().__init__(child)
        self.payload.update(step=step, total=total, path=path, logger=logger)

    @contextmanager
    def scope(self, ctx: Context) -> Iterator[Context]:
        p = self.payload
        logger = str(p["logger"])
        tag = f"[{p['path']}] step {p['step']}/{p['total']}"
        _emit_log(ctx, "info", logger, f"{tag} start")
        try:
            yield ctx
        except BaseException as exc:
            _emit_log(ctx, "warning", logger, f"{tag} failed: {exc}")
            raise
        else:
            _emit_log(ctx, "info", logger, f"{tag} done")


# --- rewrites ----------------------------------------------------------------


def annotate_steps(tree: Nu, *, logger: str = _STEP_LOGGER) -> Nu:
    """Wrap each child of every ``Sequential`` in a step-tracking Bracket.

    Each step logs ``start`` before it runs, ``done`` on success, ``failed`` on
    an exception (then re-raises). The step path is baked at rewrite time from
    the enclosing ``Sequential`` chain, so nested sequences read as
    ``Outer.Inner`` in the log. An already-wrapped child is left alone (idempotent).
    """

    def _walk(node: Nu, path: str) -> Nu:
        children = cast("tuple[Nu, ...]", node.children)
        if isinstance(node, Sequential) and len(children) >= 2:
            seq_path = f"{path}{type(node).__name__}"
            total = len(children)
            step = 0
            new_children: list[Nu] = []
            for child in children:
                if isinstance(child, _StepSpan):
                    new_children.append(_walk(child, f"{seq_path}."))
                else:
                    step += 1
                    walked = _walk(child, f"{seq_path}.{type(child).__name__}.")
                    new_children.append(_StepSpan(walked, step, total, seq_path, logger))
            return node.with_children(*new_children)

        if not children:
            return node
        walked_children = [_walk(child, path) for child in children]
        if all(new is old for new, old in zip(walked_children, children, strict=False)):
            return node
        return node.with_children(*walked_children)

    return _walk(tree, "")


def _literal_key(node: Nu, default: str) -> str:
    """The literal string a StrArg child carries, or ``default`` if it is dynamic."""
    if isinstance(node, LiteralQuery):
        value = node.payload.get("value")
        if isinstance(value, str):
            return value
    return default


def annotate_retries(tree: Nu, *, logger: str = _RETRY_LOGGER) -> Nu:
    """Add per-attempt logging hooks to every ``Retry`` node.

    Each ``Retry`` gets an ``on_attempt_fail`` hook that logs the failed attempt
    (its number and error string, read from ``ctx.attrs``). An existing hook is
    preserved - the log runs first, then the original (``log >> hook``).

    Only ``on_attempt_fail`` is injected, deliberately. In the v2 ``Retry`` an
    ``on_fail`` hook is a *handler*: when present, exhaustion logs then returns
    ``None`` instead of raising (see ``nu.spans.policy``). Hijacking it for a log
    line would silently swallow the terminal error, so annotation leaves it be -
    final exhaustion propagates exactly as it would unannotated. Note too that
    ``Retry`` fires hooks on the async path only, so this logging shows under
    ``arun`` / ``acollect``, not the basic sync retry.
    """

    def _annotate(node: Nu) -> Nu:
        if not isinstance(node, Retry):
            return node

        # Pinned to Retry's fixed child layout (see nu.spans.policy.Retry):
        # [body, max_attempts, delay, backoff, jitter, on_attempt_fail,
        #  on_success, on_fail, error_key, attempt_key]. Guard so a future
        # reorder fails loudly here instead of silently mislabeling.
        kids = cast("tuple[Nu, ...]", node.children)
        if len(kids) != _RETRY_ARITY:
            msg = f"Retry child layout changed ({len(kids)} children); update annotate_retries"
            raise RuntimeError(msg)
        attempt = IntAttrRef(_literal_key(kids[9], "attempt"))
        error = StrAttrRef(_literal_key(kids[8], "error"))
        log_af = log("retry attempt", attempt, "failed:", error, level="warning", logger=logger)

        existing_af, existing_success, existing_fail = kids[5], kids[6], kids[7]
        on_attempt_fail = log_af if isinstance(existing_af, Noop) else (log_af >> existing_af)

        return Retry(
            kids[0],
            max_attempts=kids[1],
            delay=kids[2],
            backoff=kids[3],
            jitter=kids[4],
            errors=cast("tuple[type[Exception], ...] | None", node.payload.get("errors")),
            on_attempt_fail=cast("Hook", on_attempt_fail),
            on_success=None if isinstance(existing_success, Noop) else cast("Hook", existing_success),
            on_fail=None if isinstance(existing_fail, Noop) else cast("Hook", existing_fail),
            error_key=kids[8],
            attempt_key=kids[9],
        )

    return map_nodes(tree, _annotate, order="bottom_up")


def set_logger_name(tree: Nu, name: str) -> Nu:
    """Retarget the logger on every step span and ``LogCommand`` in the tree.

    Renames the ``logger`` a step Bracket logs under and swaps the logger child
    (slot 2) of every ``LogCommand`` - so a whole annotated tree logs under one
    chosen name.
    """

    def _rename(node: Nu) -> Nu:
        if isinstance(node, _StepSpan):
            p = node.payload
            body = cast("Nu", node.children[0])
            return _StepSpan(body, cast("int", p["step"]), cast("int", p["total"]), str(p["path"]), name)
        if isinstance(node, LogCommand):
            return node.with_children(
                node.children[0],
                node.children[1],
                LiteralQuery(name),
                *node.children[3:],
            )
        return node

    return map_nodes(tree, _rename, order="bottom_up")
