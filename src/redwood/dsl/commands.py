"""Command term implementations.

CommandTerms represent impure operations with side effects:
- DeleteCommand: Delete a path
- UpdateCommand: Update a value based on current value
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from redwood.dsl.term import CommandTerm, PathTerm
from redwood.dsl.types import Empty, is_special


if TYPE_CHECKING:
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree


class DeleteCommand(CommandTerm):
    """Delete command: path.delete().

    Deletes the value at the specified path through the parent view's
    .delete() method.

    Example:
        User.age.delete().evaluate(tree, ctx)
    """

    def __init__(self, path: PathTerm) -> None:
        """Initialize delete command.

        Args:
            path: Path to delete
        """
        super().__init__()
        self.path = path

        # Inherit dependencies from path
        self.meta.dependencies = path.meta.dependencies

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> None:
        """Execute delete command through parent view.

        Navigation strategy:
        1. Resolve path to segments
        2. Navigate to parent (all segments except last)
        3. Get parent view
        4. Call view.delete(last_segment)

        Args:
            tree: Tree instance
            ctx: Context (must support writes)

        Returns:
            None (deletion has no return value)
        """
        try:
            # Resolve path
            path_components = self.path.resolve_path(tree, ctx)

            if not path_components:
                raise ValueError("Cannot delete root path")

            # Get view type (default to DictView)
            from redwood.tree.view import DictView

            if hasattr(self.path, "_parent_view_type"):
                view_type = self.path._parent_view_type
            else:
                view_type = DictView

            # Single segment - delete from root
            if len(path_components) == 1:
                view = tree.view(view_type, ctx=ctx)
                view.remove(path_components[0])
                return

            # Multiple segments - navigate to parent
            parent_path = path_components[:-1]
            final_key = path_components[-1]

            # Navigate to parent container
            current = tree
            for segment in parent_path:
                current = current.at(segment)

            # Get parent view and delete
            view = current.view(view_type, ctx=ctx)
            view.remove(final_key)

        except (KeyError, AttributeError, IndexError):
            # Graceful failure - already deleted or doesn't exist
            pass


class UpdateCommand(CommandTerm):
    """Update command: path.update(fn).

    Updates a value based on its current value through a transformation function.
    Reads current value, applies function, then sets result.

    Example:
        User.age.update(lambda x: x + 1).evaluate(tree, ctx)
    """

    def __init__(self, path: PathTerm, fn: Callable[[Any], Any]) -> None:
        """Initialize update command.

        Args:
            path: Path to update
            fn: Transformation function (current_value) -> new_value
        """
        super().__init__()
        self.path = path
        self.fn = fn

        # Inherit dependencies from path
        self.meta.dependencies = path.meta.dependencies

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> Any:
        """Execute update command: read, transform, write.

        Args:
            tree: Tree instance
            ctx: Context (must support reads and writes)

        Returns:
            New value after update, or Empty on failure
        """
        try:
            # Read current value
            from redwood.dsl.operations import GetOperation
            from redwood.tree.view import DictView

            # Get view type
            if hasattr(self.path, "_parent_view_type"):
                view_type = self.path._parent_view_type
            else:
                view_type = DictView

            get_op = GetOperation(self.path, view_type)
            current_value = get_op.evaluate(tree, ctx)

            if is_special(current_value):
                return Empty  # Can't update non-existent value

            # Apply transformation
            try:
                new_value = self.fn(current_value)
            except Exception:
                return Empty  # Transformation failed

            # Write back through set operation
            from redwood.dsl.operations import SetOperation

            set_op = SetOperation(self.path, new_value, view_type)
            set_op.evaluate(tree, ctx)

            return new_value

        except (KeyError, AttributeError):
            return Empty
