from __future__ import annotations

import pytest

from everyast import Node


class SimpleNode(Node):
    """Concrete node for testing."""

    __slots__ = ("_children", "_label")

    def __init__(self, label, *children):
        self._label = label
        self._children = children

    @property
    def label(self):
        return self._label

    @property
    def children(self):
        return self._children

    def with_children(self, *children):
        if not children and not self._children:
            return self
        return SimpleNode(self._label, *children)

    def __repr__(self):
        if self._children:
            return f"SimpleNode({self._label!r}, ...{len(self._children)})"
        return f"SimpleNode({self._label!r})"

    def __eq__(self, other):
        if not isinstance(other, SimpleNode):
            return NotImplemented
        return self._label == other._label and self._children == other._children


@pytest.fixture
def tree():
    """Sample tree:

         a
        / \\
       b   c
      / \\   \\
     d   e   f
    """
    d = SimpleNode("d")
    e = SimpleNode("e")
    f = SimpleNode("f")
    b = SimpleNode("b", d, e)
    c = SimpleNode("c", f)
    a = SimpleNode("a", b, c)
    return a
