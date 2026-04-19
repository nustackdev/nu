"""Keyboard echo loop with termination handling.

Raw stdio fabric API - StdioWrite, StdioRead, StdioFlush.
No Print/Log/Debug aliases. Real stdin/stdout/stderr.

Type lines, get them echoed back. "quit" to exit.
Ctrl+C writes to stderr and exits cleanly.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import nu
from nu import Context, DoWhile, If, NeOp, StrAttrRef, TryCatch
from nu.stdio import STDERR, STDIN, STDOUT, StdioFlush, StdioRead, StdioWrite
from nu.terms.effect import tracked_effects
from nu.terms.op import Command


if TYPE_CHECKING:
    from nu.context import Context as Ctx


class StoreAttr(Command):
    """Store child[1] result into ctx.attrs[child[0]]."""

    def __init__(self, key: str, value: object) -> None:
        super().__init__(key, value)

    async def run(self, ctx: Ctx) -> None:
        key = await self.children[0].first(ctx)
        val = await self.children[1].first(ctx)
        if key is not None:
            ctx.attrs[key] = val


def build_tree():
    """Build the echo loop tree."""
    line = StrAttrRef("line")

    return TryCatch(
        body=DoWhile(
            condition=NeOp(line, "quit"),
            body=(
                StdioWrite(STDOUT, "> ")
                >> StdioFlush(STDOUT)
                >> StoreAttr("line", StdioRead(STDIN))
                >> If(
                    NeOp(line, "quit"),
                    StdioWrite(STDOUT, "echo:", line),
                )
            ),
        ),
        catch=StdioWrite(STDERR, "error:", StrAttrRef("error")),
        finally_=StdioWrite(STDOUT, "bye."),
    )


if __name__ == "__main__":
    tree = build_tree()
    print(f"effects: {tracked_effects(tree)}")
    print()
    asyncio.run(tree.execute(Context()))
