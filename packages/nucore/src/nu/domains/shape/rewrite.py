"""Re-rooting: splice every bare ref chain in a tree under a new parent.

A snippet author writes slots without knowing where they live::

    class Section(nu.Shape):
        inp = nustd.ui.InputRef.slot()

    def out():
        return Section.inp.set("whatever")

``Section.inp`` is a chain root, so it resolves bare, at ``("inp",)``. The
host that owns the snippet knows where it belongs and says so afterwards, by
rewriting the term between constructing it and evaluating it: every chain
root gets the host's parent ref spliced in where its :data:`~nu.domains.shape.refs.base.ANCHOR`
was, so the whole chain resolves one level deeper.

This works because a ref's parent is ``children[0]`` of an immutable term,
not an attribute on a live object. Addressing walks that link at run time, so
a rewritten tree simply resolves somewhere else - there is no object graph to
fix up and no precomputed path to invalidate. The source chain is untouched,
which is what lets the same ``Section.inp`` be spliced under two different
parents in two different terms.

Policy is the caller's
----------------------

Which parent, and which chains are exempt, are both arguments. ``rooted`` is
the exemption: a predicate asked about each chain root, answering "the author
rooted this one deliberately, leave it alone". That is how one block reaches
another on purpose - it names the other block's root explicitly, and the
rewrite passes it by. A chain the predicate claims is still *recursed into*,
because a dynamic address inside it is its own chain and is judged on its own.

Two things to get right
-----------------------

- Every child is recursed into, with no exception for a level's address. A
  dynamic index that is itself a ref (``Shop.orders[Cursor.current]``) is a
  chain like any other, and leaving it alone resolves it against the old
  root while the spine around it moved.
- ``root_shape`` is rebuilt on every node. It no longer contributes to an
  address, but it is still the tag that routes a write to a navigator and
  scopes ``auto_flow_atomic``, so a spliced chain has to pick up the tag of
  the parent it landed under. Stale is invisible under a default navigator
  and wrong under a tagged one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .refs.base import StructuredRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.tree import Transform


__all__ = ["reroot", "rerooter"]


def reroot(
    root: Nu,
    under: StructuredRef,
    *,
    rooted: Callable[[StructuredRef], bool] | None = None,
) -> Nu:
    """Rewrite ``root`` so every bare ref chain in it hangs off ``under``.

    Args:
        root: the tree to rewrite. Any Nu term, not only a ref.
        under: the ref the bare chains are spliced under. Its own chain and
            its ``root_shape`` come along, so a chain rewritten under
            ``World.shop`` resolves at ``("shop", ...)`` and routes to
            whatever navigator ``World`` is tagged with.
        rooted: predicate asked about each chain root (the ref whose parent
            is the ANCHOR). True means the author rooted that chain on
            purpose and it is left where it is. With none given every chain
            is spliced.

    Notes:
        - Non-ref nodes are walked through, so a ref buried under flows,
          spans and interactions is reached the same as one at the top.
        - A level's address child is recursed into like any other, so a
          dynamic index that is itself a ref moves with the spine.
        - An exempt chain is passed by but still recursed into: an address
          inside it is a separate chain and gets its own answer.
        - Subtrees that come back unchanged are returned by identity, so an
          already-rooted term is the same object it went in as.
        - Payload is copied per rebuilt node rather than shared, because
          ``_with_children`` aliases the dict and writing ``root_shape``
          into it would corrupt the chain the snippet still holds.

    Returns:
        The rewritten tree. ``root`` itself is untouched.

    Example:
        >>> term = Section.inp.set("hi")
        >>> reroot(term, Page.sections["form"])
        # resolves at ("sections", "form", "inp")
    """

    def splice(node: StructuredRef) -> Nu:
        kids = node._children
        head = kids[0]
        if isinstance(head, StructuredRef):
            parent: Nu = walk(head)
        elif rooted is not None and rooted(node):
            parent = head
        else:
            parent = under
        rest = tuple(walk(c) for c in kids[1:])
        scope = parent._root_shape if isinstance(parent, StructuredRef) else node._root_shape
        if (
            parent is head
            and scope is node._root_shape
            and all(new is old for new, old in zip(rest, kids[1:], strict=True))
        ):
            return node
        variant = node._with_children(parent, *rest)
        variant._payload = {**node._payload, "root_shape": scope}
        return variant

    def walk(node: Nu) -> Nu:
        if isinstance(node, StructuredRef):
            return splice(node)
        if not node._children:
            return node
        kids = tuple(walk(c) for c in node._children)
        if all(new is old for new, old in zip(kids, node._children, strict=True)):
            return node
        return node._with_children(*kids)

    return walk(root)


def rerooter(
    under: StructuredRef,
    *,
    rooted: Callable[[StructuredRef], bool] | None = None,
) -> Transform:
    """:func:`reroot` with its policy fixed, as a plain ``Nu -> Nu`` transform.

    The form a rewrite slot takes: bind the parent and the exemption once,
    hand the result to whatever produces the term.

    Args:
        under: the ref bare chains are spliced under.
        rooted: predicate exempting chain roots the author placed himself.

    Returns:
        A transform that re-roots any tree handed to it.

    Example:
        >>> nu.LoadNu(src, rewrite=rerooter(Page.sections[name]))
    """

    def transform(root: Nu) -> Nu:
        return reroot(root, under, rooted=rooted)

    return transform
