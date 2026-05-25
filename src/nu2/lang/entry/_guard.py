"""Guard against driving an async-only Program from a sync entry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang.structure import Attr


if TYPE_CHECKING:
    from nu2.engine import Program


def refuse_async_only(program: Program, entry: str, swap: str) -> None:
    """Raise if a sync entry sees an async-only subtree.

    Reads the root's ``Attr.HAS_ASYNC_ONLY_ATOM`` column directly; one list
    index, no schema lookup.
    """
    if program.attrs[Attr.HAS_ASYNC_ONLY_ATOM][0]:
        msg = f"{entry}: program contains an async-only atom (e.g. Watch); use {swap}."
        raise RuntimeError(msg)
