"""
Path resolution engine.

This module provides the PathResolver class that handles the core responsibility
of resolving path components against tree data. The resolver uses a three-phase
approach to navigate efficiently through the tree structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from .exceptions import PathEvaluationError, PathNotFoundError
from .types import PathResult

if TYPE_CHECKING:
    from ..tree import Tree
    from .path import Path

__all__ = [
    "PathResolver",
]


class PathResolver:
    """
    Core path resolution engine.

    The PathResolver has one primary responsibility: given a path and tree,
    resolve the path components to retrieve the actual value from the tree.

    Resolution Strategy:
    The resolver uses a three-phase approach optimized for the tree's architecture:

    1. **Tree Navigation Phase**: Navigate through leading string components
       using tree.at() calls until we reach containers that need view access

    2. **View Navigation Phase**: Use appropriate views (dict/list) to navigate
       through mixed component types, creating and chaining views as needed

    3. **Value Extraction Phase**: Extract the final value from the last view
       using the final component as key/index

    This approach minimizes view creation overhead while handling complex
    navigation patterns efficiently.
    """

    def resolve(self, path: "Path", tree: "Tree", ctx: Any = None) -> PathResult:
        """
        Resolve path to its value in the tree.

        Args:
            path: Path object containing components to navigate
            tree: Tree instance to navigate
            ctx: Optional context (transaction/snapshot)

        Returns:
            Value at the path location

        Raises:
            PathNotFoundError: If path doesn't exist
            PathEvaluationError: If resolution fails
        """
        components = path.components

        try:
            if not components:
                raise PathNotFoundError("Empty path cannot be resolved")

            # Phase 1: Navigate tree with leading string components
            i = 0
            while i < len(components) - 1 and isinstance(components[i], str):
                i += 1

            str_components = cast(tuple[str, ...], components[:i])

            current_tree = tree.at(*str_components, ctx=ctx) if i > 0 else tree
            current_view = None

            # Phase 2: Navigate through views for remaining components
            while i < len(components) - 1:
                component = components[i]
                next_component = components[i + 1]

                if current_view is None:
                    current_view = self._create_view_for_next(current_tree, next_component, ctx)

                current_view = self._navigate_view(current_view, component, next_component)
                i += 1

            # Phase 3: Extract final value
            last_component = components[-1]
            if current_view is None:
                current_view = self._create_view_for_component(current_tree, last_component, ctx)

            return current_view.get(last_component)

        except Exception as e:
            if isinstance(e, PathNotFoundError):
                raise
            raise PathEvaluationError(
                f"Failed to resolve path {self._format_path_components(components)}",
                path=path,
                original_error=e,
            ) from e

    def _create_view_for_next(self, tree: Tree, next_component: str | int, ctx: Any) -> Any:
        """
        Create view based on what the next component needs.

        Args:
            tree: Tree instance to create view from
            next_component: Next component in path (determines view type)
            ctx: Optional context

        Returns:
            DictView if next component is string, ListView if integer
        """
        if isinstance(next_component, str):
            return tree.dict_view(ctx=ctx)
        elif isinstance(next_component, int):
            return tree.list_view(ctx=ctx)
        else:
            raise PathEvaluationError(f"Unsupported component type: {type(next_component)}")

    def _create_view_for_component(self, tree: Tree, component: str | int, ctx: Any) -> Any:
        """
        Create view based on the component type.

        Args:
            tree: Tree instance to create view from
            component: Component to access (determines view type)
            ctx: Optional context

        Returns:
            DictView if component is string, ListView if integer
        """
        if isinstance(component, str):
            return tree.dict_view(ctx=ctx)
        elif isinstance(component, int):
            return tree.list_view(ctx=ctx)
        else:
            raise PathEvaluationError(f"Unsupported component type: {type(component)}")

    def _navigate_view(self, view: Any, component: str | int, next_component: str | int) -> Any:
        """
        Navigate view to next container based on next component type.

        Args:
            view: Current view to navigate from
            component: Current component to navigate through
            next_component: Next component (determines target view type)

        Returns:
            Next view accessed through component
        """
        if isinstance(next_component, str):
            return view.dict_view(component)
        elif isinstance(next_component, int):
            return view.list_view(component)
        else:
            raise PathEvaluationError(f"Unsupported next component type: {type(next_component)}")

    def _format_path_components(self, components: tuple) -> str:
        """
        Format path components for error messages.

        Args:
            components: Tuple of path components

        Returns:
            Formatted string representation of path
        """
        if not components:
            return "root"
        return ".".join(str(c) for c in components)
