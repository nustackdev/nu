"""ABC meta-transforms — tree rewrites using abc-specific constructs."""

from __future__ import annotations

import logging

from nu import Span, map_nodes
from nu.terms import Op
from nu.interfaces import StrI
from nu.ops import ToStrOp
from nu.terms import Nu


__all__ = [
    "annotate_retries",
    "annotate_steps",
    "set_logger_name",
]

_step_logger = logging.getLogger("everybase.steps")


class _StepSpan(Span):
    """Wraps a Seq child to log step progress. Path is baked at construction."""

    def __init__(self, child: Nu, step: int, total: int, path: str) -> None:
        super().__init__(child)
        self._step = step
        self._total = total
        self._path = path
        self._logger_name = "everybase.steps"

    def _log(self, level: str, msg: str, *args: object) -> None:
        logging.getLogger(self._logger_name).log(logging.getLevelName(level), msg, *args)

    def enter(self, ctx: object) -> object:
        self._log("INFO", "[%s] step %d/%d start", self._path, self._step, self._total)
        return ctx

    def exit_success(self, ctx: object) -> None:
        self._log("INFO", "[%s] step %d/%d done", self._path, self._step, self._total)

    def exit_failure(self, ctx: object, error: BaseException) -> None:
        self._log(
            "WARNING",
            "[%s] step %d/%d failed: %s",
            self._path,
            self._step,
            self._total,
            error,
        )


def annotate_retries[N: Nu](tree: N) -> N:
    """Add logging hooks to all Retry nodes.

    Wraps every Retry with Log-based hooks for ``on_attempt_fail`` and
    ``on_fail``.  If the Retry already has hooks, they are preserved —
    a ``Seq(Log(...), existing_hook)`` wraps the original.

    Args:
        tree: Tree root.

    Returns:
        New tree with annotated Retry nodes.
    """
    from nu.ops import Log, Retry, Seq

    from ..refs import IntRef, StrRef

    def _annotate(node: Nu) -> Nu:
        if not isinstance(node, Retry):
            return node

        error = StrRef("error")
        attempt = IntRef("attempt")

        log_af = Log(
            "retry attempt " + StrI(ToStrOp(attempt.get())) + " failed: " + error.get(),
            level="warning",
        )
        log_fail = Log(
            "retry exhausted after "
            + StrI(ToStrOp(attempt.get()))
            + " attempts: "
            + error.get(),
            level="error",
        )

        existing_af = node.on_attempt_fail
        existing_fail = node.on_fail

        on_af = Seq(log_af, existing_af) if existing_af else log_af
        on_fail = Seq(log_fail, existing_fail) if existing_fail else log_fail

        return node.with_children(
            *node.children[:4],
            on_af,
            node.children[5],  # on_success — unchanged
            on_fail,
        )

    return map_nodes(tree, _annotate, order="bottom_up")


def annotate_steps[N: Nu](tree: N) -> N:
    """Wrap Seq children in step-tracking spans with baked tree paths.

    Walks the tree recursively, tracking the structural path from root.
    Each Flow/Span child of a Seq gets wrapped in a ``_StepSpan`` with
    the path baked in.  All ``Log`` nodes encountered get their ``_path``
    set so log messages show their tree position.

    Args:
        tree: Tree root.

    Returns:
        New tree with step-annotated Seq nodes and path-aware Log nodes.
    """
    from nu.ops import Log, Seq

    def _walk(node: Nu, path: str) -> Nu:
        # Seq with meaningful children: wrap Flow/Span children in _StepSpan
        if isinstance(node, Seq):
            meaningful = [c for c in node.children if isinstance(c, (Op, Span))]
            if len(meaningful) >= 2:
                seq_path = f"{path}{type(node).__name__}"
                total = len(meaningful)
                step = 0
                new_children: list = []
                for child in node.children:
                    if isinstance(child, (Op, Span)) and not isinstance(child, _StepSpan):
                        step += 1
                        name = type(child).__name__
                        walked = _walk(child, f"{seq_path}.{name}.")
                        new_children.append(
                            _StepSpan(walked, step, total, path=seq_path),
                        )
                    else:
                        new_children.append(_walk(child, f"{seq_path}."))
                return node.with_children(*new_children)

        # Log nodes: bake the current path
        if isinstance(node, Log) and path:
            clone = node.with_children(*node.children)
            clone._path = path.rstrip(".")
            return clone

        # Recurse into children
        if not node.children:
            return node
        new_children = [_walk(child, path) for child in node.children]
        if all(new is old for new, old in zip(new_children, node.children, strict=False)):
            return node
        return node.with_children(*new_children)

    return _walk(tree, "")


def set_logger_name[N: Nu](tree: N, name: str) -> N:
    """Rename the logger on all Log nodes in the tree.

    Args:
        tree: Tree root.
        name: Logger name to set (e.g. ``"mytool.myapp"``).

    Returns:
        New tree with renamed Log nodes.
    """
    from nu.ops import Log

    def _rename(node: Nu) -> Nu:
        if not isinstance(node, (Log, _StepSpan)):
            return node
        clone = node.with_children(*node.children)
        clone._logger_name = name
        return clone

    return map_nodes(tree, _rename, order="bottom_up")
