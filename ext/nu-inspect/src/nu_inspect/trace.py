"""Annotation transforms -- logging and step-tracking tree rewrites."""

from __future__ import annotations

import logging
from typing import ClassVar

from nu.context import Context, IntAttrRef, StrAttrRef
from nu.interactions import Log, Retry, ToStr
from nu.terms import Literal, Mode, Nu
from nu.terms.flow import Sequential
from nu.terms.span import Bracket
from nu.tree import map_nodes


__all__ = [
    "annotate_retries",
    "annotate_steps",
    "set_logger_name",
]

_step_logger = logging.getLogger("nu.steps")


class _StepSpan(Bracket):
    """Wraps a sequential child to log step progress. Path is baked at construction."""

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, child: Nu, step: int, total: int, path: str) -> None:
        super().__init__(child)
        self._step = step
        self._total = total
        self._path = path
        self._logger_name = "nu.steps"

    def _log(self, level: str, msg: str, *args: object) -> None:
        logging.getLogger(self._logger_name).log(logging.getLevelName(level), msg, *args)

    def before(self, ctx: Context) -> Context:
        self._log("INFO", "[%s] step %d/%d start", self._path, self._step, self._total)
        return ctx

    def after(self, ctx: Context) -> None:
        self._log("INFO", "[%s] step %d/%d done", self._path, self._step, self._total)

    def after_failure(self, ctx: Context, error: BaseException) -> None:
        self._log(
            "WARNING",
            "[%s] step %d/%d failed: %s",
            self._path,
            self._step,
            self._total,
            error,
        )


def annotate_retries(tree: Nu) -> Nu:
    """Add logging hooks to all Retry nodes.

    Wraps every Retry with Log-based hooks for ``on_attempt_fail`` and
    ``on_fail``. If the Retry already has hooks, they are preserved --
    a ``Log(...) >> existing_hook`` wraps the original.
    """

    def _annotate(node: Nu) -> Nu:
        if not isinstance(node, Retry):
            return node

        error = StrAttrRef("error")
        attempt = IntAttrRef("attempt")

        log_af = Log(
            "retry attempt " + ToStr(attempt.get()) + " failed: " + error.get(),
            level="warning",
        )
        log_fail = Log(
            "retry exhausted after " + ToStr(attempt.get()) + " attempts: " + error.get(),
            level="error",
        )

        existing_af = node.on_attempt_fail
        existing_fail = node.on_fail

        on_af = (log_af >> existing_af) if existing_af else log_af
        on_fail = (log_fail >> existing_fail) if existing_fail else log_fail

        # Rebuild the Retry preserving its body and config, replacing hooks.
        body = node._children[0]
        return Retry(
            body,
            max_attempts=node._max_attempts,
            delay=node._delay,
            backoff=node._backoff,
            on_attempt_fail=on_af,
            on_success=node.on_success,
            on_fail=on_fail,
        )

    return map_nodes(tree, _annotate, order="bottom_up")


def annotate_steps(tree: Nu) -> Nu:
    """Wrap sequential composition children in step-tracking spans with baked tree paths."""

    def _walk(node: Nu, path: str) -> Nu:
        if isinstance(node, Sequential):
            if len(node._children) >= 2:
                seq_path = f"{path}{type(node).__name__}"
                total = len(node._children)
                step = 0
                new_children: list = []
                for child in node._children:
                    if not isinstance(child, _StepSpan):
                        step += 1
                        name = type(child).__name__
                        walked = _walk(child, f"{seq_path}.{name}.")
                        new_children.append(
                            _StepSpan(walked, step, total, path=seq_path),
                        )
                    else:
                        new_children.append(_walk(child, f"{seq_path}."))
                return node._with_children(tuple(new_children))

        if isinstance(node, Log) and path:
            clone = node._with_children(node._children)
            clone._path = path.rstrip(".")
            return clone

        if not node._children:
            return node
        new_children = [_walk(child, path) for child in node._children]
        if all(new is old for new, old in zip(new_children, node._children, strict=False)):
            return node
        return node._with_children(tuple(new_children))

    return _walk(tree, "")


def set_logger_name(tree: Nu, name: str) -> Nu:
    """Rename the logger on all Log nodes in the tree."""

    def _rename(node: Nu) -> Nu:
        if not isinstance(node, (Log, _StepSpan)):
            return node
        new_children = (
            *node._children[:2],
            Literal(name),
            *node._children[3:],
        )
        return node._with_children(new_children)

    return map_nodes(tree, _rename, order="bottom_up")
