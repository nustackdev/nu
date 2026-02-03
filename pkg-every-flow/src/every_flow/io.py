"""I/O flows — side-effectful flows for debugging and output.

Print: execute a child Term and print its result with a label.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Flow


if TYPE_CHECKING:
    from everybase import Term


__all__ = [
    "Print",
]


class Print(Flow):
    """Execute a child Term and print its result.

    Wraps a single Term child. On execute, evaluates the child
    and prints ``[label] value`` to stdout.

    Args:
        label: Prefix shown in output (e.g. field name).
        child: Term whose result is printed.

    Example::

        Print("name", AppState.name.get())
        # Output: [name] 'Alice'
    """

    def __init__(self, label: str, child: Term) -> None:
        super().__init__(child)
        self.label = label

    async def execute(self, ctx: object) -> None:
        """Evaluate the child Term and print its result."""
        value = await self.children[0].execute(ctx)
        print(f"  [{self.label}] {value!r}")  # noqa: T201
