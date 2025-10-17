"""Operation terms for reading and writing values.

Operations delegate to view protocols for all tree access.
All access goes through parent views, never directly to storage.
"""

from typing import TYPE_CHECKING

from redwood.dsl.term import CommandTerm, PathTerm, ValueTerm
from redwood.dsl.types import Empty, SpecialValue


if TYPE_CHECKING:
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree


class GetOperation[T](ValueTerm):
    """Pure read operation - reads value through parent view.

    Gets the value at a path by navigating to the parent container
    and calling the parent view's .get() method.

    Example:
        op = User.age.get()
        value = op.evaluate(tree, ctx)  # Returns int via parent view
    """

    def __init__(self, path: PathTerm, view_type: type) -> None:
        """Initialize get operation.

        Args:
            path: Path to read from
            view_type: View type of the parent container
        """
        super().__init__()
        self.path = path
        self.view_type = view_type

        # Inherit metadata from path
        self.meta.value_type = path.meta.primitive_type
        self.meta.dependencies = path.meta.dependencies

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> T | SpecialValue:
        """Read value through parent view.

        Navigation strategy:
        1. Resolve path to segments
        2. Navigate to parent (all segments except last)
        3. Get parent view
        4. Call view.get(last_segment)

        Args:
            tree: Tree instance
            ctx: Context for data access

        Returns:
            Value at path (type T), or Empty if not found
        """
        try:
            # Resolve path
            path_components = self.path.resolve_path(tree, ctx)

            if not path_components:
                return Empty

            # Single segment - read from root
            if len(path_components) == 1:
                view = tree.view(self.view_type, ctx=ctx)
                result = view.get(path_components[0])
                return result if result is not None else Empty

            # Multiple segments - navigate to parent
            parent_path = path_components[:-1]
            final_key = path_components[-1]

            # Navigate to parent container
            current = tree
            for segment in parent_path:
                current = current.at(segment)

            # Get parent view and read
            view = current.view(self.view_type, ctx=ctx)
            result = view.get(final_key)
            return result if result is not None else Empty

        except (KeyError, AttributeError, IndexError):
            # Graceful failure - return Empty
            return Empty


class SetOperation(CommandTerm):
    """Impure write operation - writes value through parent view.

    Sets the value at a path by navigating to the parent container
    and calling the parent view's .set() method.

    Example:
        op = User.age.set(30)
        op.evaluate(tree, ctx)  # Writes via parent view
    """

    def __init__(self, path: PathTerm, value: object, view_type: type) -> None:
        """Initialize set operation.

        Args:
            path: Path to write to
            value: Value to set
            view_type: View type of the parent container
        """
        super().__init__()
        self.path = path
        self.value = value
        self.view_type = view_type

        # Inherit metadata from path
        self.meta.dependencies = path.meta.dependencies

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> None:
        """Write value through parent view.

        Navigation strategy:
        1. Resolve path to segments
        2. Navigate to parent (all segments except last)
        3. Get parent view
        4. Call view.set(last_segment, value)

        Args:
            tree: Tree instance
            ctx: Context for data access (must support writes)

        Returns:
            None (side effect operation)
        """
        try:
            # Resolve path
            path_components = self.path.resolve_path(tree, ctx)

            if not path_components:
                raise ValueError("Cannot set root path")

            # Single segment - write to root
            if len(path_components) == 1:
                view = tree.view(self.view_type, ctx=ctx)
                view.set(path_components[0], self.value)
                return

            # Multiple segments - navigate to parent
            parent_path = path_components[:-1]
            final_key = path_components[-1]

            # Navigate to parent container
            current = tree
            for segment in parent_path:
                current = current.at(segment)

            # Get parent view and write
            view = current.view(self.view_type, ctx=ctx)
            view.set(final_key, self.value)

        except (KeyError, AttributeError, IndexError):
            # Let write errors propagate - these are real issues
            raise
