"""Command term implementations.

CommandTerms represent impure operations with side effects:
- SetCommand: Set a value at a path
- DeleteCommand: Delete a path
- UpdateCommand: Update a value based on current value
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from redwood.dsl.exceptions import DSLPathError, DSLViewError
from redwood.dsl.metadata import TermMetadata
from redwood.dsl.term import CommandTerm, PathTerm, ValueTerm
from redwood.dsl.types import Empty, TermResult, is_special


if TYPE_CHECKING:
    from redwood.tree import ContextType, Tree

__all__ = ["DeleteCommand", "SetCommand", "UpdateCommand"]


@dataclass(frozen=True)
class SetCommand(CommandTerm):
    """Set command: path.set(value).

    Sets a value at the specified path through the parent view's .set() method.

    Attributes:
        path: Path to set
        value: Value to set (can be literal or ValueTerm)
    """

    path: PathTerm
    value: Any  # Can be literal or ValueTerm

    def __init__(self, path: PathTerm, value: Any) -> None:
        """Initialize set command.

        Args:
            path: Path to set
            value: Value to set
        """
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "value", value)

        super(CommandTerm, self).__init__()

        # Merge dependencies from path and value (if value is term)
        dependencies = path.meta.dependencies
        if isinstance(value, ValueTerm):
            dependencies = dependencies | value.meta.dependencies

        meta = TermMetadata(
            is_pure=False,
            has_side_effects=True,
            dependencies=dependencies,
        )
        object.__setattr__(self, "meta", meta)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Execute set command through parent view.

        Args:
            tree: Tree instance
            ctx: Context (must support writes)

        Returns:
            The value that was set, or Empty on failure

        Raises:
            DSLViewError: If view doesn't support .set()
        """
        try:
            # Resolve value if it's a term
            if isinstance(self.value, ValueTerm):
                resolved_value = self.value.evaluate(tree, ctx)
                if is_special(resolved_value):
                    return Empty  # Can't set special values
            else:
                resolved_value = self.value

            # Get parent path and last segment
            parent = self.path.parent_path()
            if parent is None:
                msg = "Cannot set root path"
                raise DSLPathError(msg)

            last_segment = self.path.last_segment()

            # Navigate to parent
            parent_segments = parent.resolve_path(tree, ctx)
            current = tree
            for segment in parent_segments:
                current = current.at(segment)

            # Get parent view
            if parent.meta.view_type is not None:
                view = current.view(parent.meta.view_type, ctx=ctx)
            else:
                from redwood.tree import DictView

                view = current.view(DictView, ctx=ctx)

            # Execute set through view
            if hasattr(view, "set"):
                view.set(last_segment, resolved_value)
                return resolved_value
            else:
                msg = f"View {type(view).__name__} doesn't support .set() operation"
                raise DSLViewError(msg)

        except (KeyError, AttributeError, DSLPathError):
            # Return Empty on failure
            return Empty


@dataclass(frozen=True)
class DeleteCommand(CommandTerm):
    """Delete command: path.delete().

    Deletes the value at the specified path through the parent view's .delete() method.

    Attributes:
        path: Path to delete
    """

    path: PathTerm

    def __init__(self, path: PathTerm) -> None:
        """Initialize delete command.

        Args:
            path: Path to delete
        """
        object.__setattr__(self, "path", path)

        super(CommandTerm, self).__init__()

        meta = TermMetadata(
            is_pure=False,
            has_side_effects=True,
            dependencies=path.meta.dependencies,
        )
        object.__setattr__(self, "meta", meta)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Execute delete command through parent view.

        Args:
            tree: Tree instance
            ctx: Context (must support writes)

        Returns:
            Empty (deletion has no return value)

        Raises:
            DSLViewError: If view doesn't support deletion
        """
        try:
            # Get parent path and last segment
            parent = self.path.parent_path()
            if parent is None:
                msg = "Cannot delete root path"
                raise DSLPathError(msg)

            last_segment = self.path.last_segment()

            # Navigate to parent
            parent_segments = parent.resolve_path(tree, ctx)
            current = tree
            for segment in parent_segments:
                current = current.at(segment)

            # Get parent view
            if parent.meta.view_type is not None:
                view = current.view(parent.meta.view_type, ctx=ctx)
            else:
                from redwood.tree import DictView

                view = current.view(DictView, ctx=ctx)

            # Execute delete through view
            if hasattr(view, "delete"):
                view.delete(last_segment)
            elif hasattr(view, "remove"):
                view.remove(last_segment)
            else:
                msg = f"View {type(view).__name__} doesn't support .delete() or .remove()"
                raise DSLViewError(msg)

            return Empty

        except (KeyError, AttributeError, DSLPathError):
            return Empty


@dataclass(frozen=True)
class UpdateCommand(CommandTerm):
    """Update command: path.update(fn).

    Updates a value based on its current value through a transformation function.
    Reads current value, applies function, then sets result.

    Attributes:
        path: Path to update
        fn: Update function (current_value) -> new_value
    """

    path: PathTerm
    fn: Callable[[Any], Any]

    def __init__(self, path: PathTerm, fn: Callable[[Any], Any]) -> None:
        """Initialize update command.

        Args:
            path: Path to update
            fn: Transformation function
        """
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "fn", fn)

        super(CommandTerm, self).__init__()

        meta = TermMetadata(
            is_pure=False,
            has_side_effects=True,
            dependencies=path.meta.dependencies,
        )
        object.__setattr__(self, "meta", meta)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Execute update command: read, transform, write.

        Args:
            tree: Tree instance
            ctx: Context (must support reads and writes)

        Returns:
            New value after update, or Empty on failure

        Raises:
            DSLViewError: If view doesn't support required operations
        """
        try:
            # Read current value
            current_value = self.path.evaluate(tree, ctx)
            if is_special(current_value):
                return Empty  # Can't update non-existent value

            # Apply transformation
            try:
                new_value = self.fn(current_value)
            except Exception:
                return Empty  # Transformation failed

            # Write back through set command
            set_cmd = SetCommand(self.path, new_value)
            return set_cmd.evaluate(tree, ctx)

        except (KeyError, AttributeError):
            return Empty
