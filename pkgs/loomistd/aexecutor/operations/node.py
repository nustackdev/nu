from __future__ import annotations

from typing import Generic, TypeVar

import networkx as nx

NodeT = TypeVar("NodeT", bound="DAGNodeMixin")


class DAGNodeMixin(Generic[NodeT]):
    """
    Mixin class that provides DAG functionality similar to anytree's NodeMixin.
    This implementation allows nodes to have multiple parents, forming a
    Directed Acyclic Graph (DAG) instead of a tree.
    """

    _dag = nx.DiGraph()  # Shared graph across all nodes

    def __init__(self) -> None:
        """Initialize the DAG node."""
        self._parents: set[NodeT] = set()
        self._children: set[NodeT] = set()
        DAGNodeMixin._dag.add_node(id(self), obj=self)

    @property
    def children(self) -> tuple[NodeT, ...]:
        """Get children of this node."""
        return tuple(self._children)

    @children.setter
    def children(self, children: tuple[NodeT, ...]) -> None:
        """Set children of this node."""
        # Remove existing children
        for child in list(self._children):
            self._remove_child(child)

        # Add new children
        for child in children:
            self._add_child(child)

    @children.deleter
    def children(self) -> None:
        """Delete all children of this node."""
        for child in list(self._children):
            self._remove_child(child)

    def _add_child(self, child: NodeT) -> None:
        """Add a child to this node."""
        if child not in self._children:
            self._children.add(child)
            child._parents.add(self)
            DAGNodeMixin._dag.add_edge(id(self), id(child))

    def _remove_child(self, child: NodeT) -> None:
        """Remove a child from this node."""
        if child in self._children:
            self._children.remove(child)
            child._parents.remove(self)
            if DAGNodeMixin._dag.has_edge(id(self), id(child)):
                DAGNodeMixin._dag.remove_edge(id(self), id(child))

    @property
    def parents(self) -> tuple[NodeT, ...]:
        """Get parents of this node."""
        return tuple(self._parents)

    def add_parent(self, parent: NodeT) -> None:
        """Add a parent to this node (DAG specific)."""
        if parent not in self._parents:
            parent._add_child(self)

    def add_child(self, child: NodeT) -> None:
        """Add a child to this node."""
        self._add_child(child)

    def is_leaf(self) -> bool:
        """Return True if this node has no children."""
        return len(self._children) == 0

    def is_root(self) -> bool:
        """Return True if this node has no parents."""
        return len(self._parents) == 0

    @property
    def ancestors(self) -> list[NodeT]:
        """Get all ancestors of this node."""
        ancestors = []
        nodes_to_visit: list[NodeT] = list(self._parents)
        visited = set()

        while nodes_to_visit:
            node = nodes_to_visit.pop(0)
            if id(node) not in visited:
                visited.add(id(node))
                ancestors.append(node)
                nodes_to_visit.extend(node._parents)

        return ancestors

    @property
    def descendants(self) -> list[NodeT]:
        """Get all descendants of this node."""
        descendants = []
        nodes_to_visit: list[NodeT] = list(self._children)
        visited = set()

        while nodes_to_visit:
            node = nodes_to_visit.pop(0)
            if id(node) not in visited:
                visited.add(id(node))
                descendants.append(node)
                nodes_to_visit.extend(node._children)

        return descendants

    def is_dag(self) -> bool:
        """Check if the graph is a DAG."""
        return nx.is_directed_acyclic_graph(DAGNodeMixin._dag)
