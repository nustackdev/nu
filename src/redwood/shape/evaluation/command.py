"""Command contract - impure RValues that perform mutations.

This module defines the Command abstract class, which serves as the
base for all impure operations in the semantics layer.

Contract:
    - Command(RValue): Impure operation with side effects
    - is_pure: Always False (enforced by base class)
    - execute(context): Performs mutation, returns None

Commands represent operations that MODIFY tree state:
    - Writing values to tree
    - Deleting nodes
    - Updating based on current state
    - Batch mutations

Commands are:
    - NOT cacheable: Different result each execution
    - Order-dependent: Execution sequence matters
    - Transactional: Should run in transaction contexts
    - NOT serializable (safely): Contains mutation logic

Design Philosophy:
    - Impurity by contract (explicit marking)
    - Returns None (side effects are the point)
    - Transactional safety (rely on tree transactions)
    - Fail fast (errors propagate)

Concrete Implementations (in behavior/commands.py):
    - SetCmd: Write value to location
    - DeleteCmd: Remove value from location
    - UpdateCmd: Read-transform-write pattern
    - BatchCmd: Atomic multi-operation

Transaction Requirement:
    Commands MUST execute within transaction contexts:

    ✓ Correct:
        with tree.transaction() as storage_ctx:
            ctx = Context(tree, storage_ctx)
            command.execute(ctx)

    ✗ Wrong:
        with tree.snapshot() as storage_ctx:
            ctx = Context(tree, storage_ctx)
            command.execute(ctx)  # Read-only context!

Example Usage:
    class SetCmd(Command):
        def execute(self, context: Context) -> None:
            # Mutate tree
            view.set(key, value)

    # Type checker knows no return value
    cmd: Command = SetCmd(ref, value)
    cmd.execute(ctx)  # Returns None

Why Separate from RValue?
    - Explicit impurity contract (Command = always impure)
    - Clear semantics (Operation vs Command distinction)
    - Better error messages (calling Command in pure context fails)
    - Transactional safety (Commands grouped together)

Why Return None?
    - Side effects are the point (not return values)
    - Prevents accidental use in expressions
    - Clear intent (this mutates, doesn't compute)
    - Type safety (can't compose with operations)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from .term import RValue


if TYPE_CHECKING:
    from ..types import Context


__all__ = [
    "Command",
]


class Command(RValue):
    """Impure RValue that performs a mutation.

    Commands modify tree state and should be executed within
    transaction contexts. They return None to emphasize that
    the side effect is the purpose.
    """

    @property
    def is_pure(self) -> bool:
        """Commands are always impure.

        Returns:
            False (commands always have side effects)
        """
        return False

    @abstractmethod
    def execute(self, context: Context) -> None:
        """Execute the command's side effect.

        Args:
            context: Execution environment (tree + storage context)

        Returns:
            None (mutation is the purpose)
        """
        ...
