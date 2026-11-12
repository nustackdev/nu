"""Places: a cell at ``(row, column)``, as the wire carries it.

The content table (``t[r, c]``) and the placed grid (``grid[r, c]``) both
address a cell by two positions, and both key a cell's ``span`` by it. The
key ``"r,c"`` is built here, once, so the two never drift: the same
refusals, the same wire text.

What differs stays with each container: a table reaches the cell through a
row (``t[r]`` is a row on the wire, then ``c`` under it), a grid sits the
cell at one segment ``"r,c"`` directly under itself.
"""

from __future__ import annotations

from nu.lang import Nu

from .descent import check_key


__all__ = ["place", "place_of", "plain_place"]


def place(owner: str, row: object, col: object, *, header: str | None = None) -> object:
    """The key ``"r,c"`` for row ``row``, column ``col``: a term when either side is one.

    Both sides are positions (``check_key(names=False)``). ``header`` is a row
    name taken as is, the content table's header row.
    """
    if header is None or not (isinstance(row, str) and row == header):
        check_key(owner, row, names=False)
    check_key(owner, col, names=False)
    if isinstance(row, Nu) or isinstance(col, Nu):
        import nu

        return nu.str(row) + nu.Str(",") + nu.str(col)
    return f"{row},{col}"


def place_of(owner: str, at: object, *, what: str = "a cell", header: str | None = None) -> object:
    """``place`` for ``at`` written as one ``(row, column)`` tuple; anything else fails loud."""
    if not isinstance(at, tuple) or len(at) != 2:
        msg = f"{what} is (row, column), not {at!r}"
        raise TypeError(msg)
    return place(owner, *at, header=header)


def plain_place(owner: str, at: object, *, what: str = "a cell", header: str | None = None) -> str:
    """``place_of`` for a key written on ``slot()``: plain ints only, no term."""
    key = place_of(owner, at, what=what, header=header)
    if isinstance(key, Nu):
        msg = (
            f"{owner} per child maps on slot() take plain places; use set_child for a computed one"
        )
        raise TypeError(msg)
    return key  # type: ignore[return-value]
