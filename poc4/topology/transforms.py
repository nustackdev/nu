"""Tree transforms — topology → topology functions.

Cross-cutting concerns as tree rewrites, not core features.
"""

from __future__ import annotations

from typing import Any

from .lang import Cond, Flow, Get, Group, Lit, Ref, Seq, Set, Term, Unit


# =============================================================================
# Logging transform
# =============================================================================


class Log(Term[None]):
    """Log a message. A Term so it composes in the tree."""

    def __init__(self, message: str) -> None:
        self.message = message

    def run(self, ctx: Any) -> None:
        """Print the log message."""
        print(f"[LOG] {self.message}")  # noqa: T201

    def __repr__(self) -> str:
        return f"Log({self.message!r})"


def add_logging(unit: Unit) -> Unit:
    """Insert log terms at Flow→child boundaries.

    Wraps each Flow child with enter/exit logs.
    Recurses into nested Flows and Groups.
    """
    if isinstance(unit, Seq):
        new_children: list[Unit] = []
        for i, child in enumerate(unit.children()):
            label = _label(child, i)
            new_children.append(Log(f"enter {label}"))
            new_children.append(add_logging(child))
            new_children.append(Log(f"exit {label}"))
        return Seq(*new_children)

    if isinstance(unit, Flow):
        # Generic flow — recurse into children
        return unit  # Par, Cond handled similarly if needed

    if isinstance(unit, Group):
        return _recurse_group(unit, add_logging)

    return unit


# =============================================================================
# Cancellation transform
# =============================================================================


class CancelFlag:
    """Shared cancellation flag."""

    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        """Set cancellation flag."""
        self.cancelled = True


class CheckCancelled(Term[bool]):
    """Check if cancellation has been requested."""

    def __init__(self, flag: CancelFlag) -> None:
        self.flag = flag

    def run(self, ctx: Any) -> bool:
        """Return True if cancelled."""
        return self.flag.cancelled

    def __repr__(self) -> str:
        return "CheckCancelled()"


class RaiseCancelled(Term[None]):
    """Raise CancelledError."""

    def run(self, ctx: Any) -> None:
        """Raise cancellation error."""
        raise CancelledError

    def __repr__(self) -> str:
        return "RaiseCancelled()"


class CancelledError(Exception):
    """Raised when execution is cancelled."""


class Noop(Term[None]):
    """No operation. Returns None."""

    def run(self, ctx: Any) -> None:
        """Do nothing."""

    def __repr__(self) -> str:
        return "Noop()"


def add_cancellation(unit: Unit, flag: CancelFlag) -> Unit:
    """Insert cancellation checks at Flow→child boundaries.

    Each child of a Flow gets a Cond that checks the flag first.
    """
    if isinstance(unit, Seq):
        new_children: list[Unit] = []
        for child in unit.children():
            # Check before each step
            new_children.append(
                Cond(CheckCancelled(flag), RaiseCancelled(), add_cancellation(child, flag)),
            )
        return Seq(*new_children)

    if isinstance(unit, Flow):
        return unit

    if isinstance(unit, Group):
        return _recurse_group(unit, lambda u: add_cancellation(u, flag))

    return unit


# =============================================================================
# Helpers
# =============================================================================


def _label(unit: Unit, index: int) -> str:
    """Create a readable label for a unit."""
    if isinstance(unit, Get):
        return f"Get({unit.ref.key})"
    if isinstance(unit, Set):
        return f"Set({unit.ref.key})"
    if isinstance(unit, Ref):
        return f"Ref({unit.key})"
    if isinstance(unit, Lit):
        return f"Lit({unit.value!r})"
    name = type(unit).__name__
    return f"{name}[{index}]"


def _recurse_group(group: Group, transform: Any) -> Group:
    """Apply a transform recursively into a Group's children."""
    from .lang import Atomic, GroupedContext, RootGroup

    if isinstance(group, Atomic):
        new_children = [transform(c) for c in group.children()]
        return Atomic(*new_children)
    if isinstance(group, GroupedContext):
        new_children = [transform(c) for c in group.children()]
        return GroupedContext(group.ctx_type, *new_children)
    if isinstance(group, RootGroup):
        return RootGroup(group.substrates, transform(group.child))

    return group
