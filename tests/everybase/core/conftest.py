from __future__ import annotations

import pytest

from nu import Nu


class SimpleNode(Nu):
    """Concrete Nu for testing with extra state (label)."""

    def __init__(self, label, *children):
        super().__init__(*children)
        self._label = label

    async def execute(self, ctx):
        return self._label

    @property
    def is_self_pure(self):
        return True

    @property
    def label(self):
        return self._label

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
