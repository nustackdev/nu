"""`nu demo` — list bundled demos, or run one by name."""

from __future__ import annotations

import ast
import runpy
import sys
from typing import TYPE_CHECKING

import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from nu._cli._meta import demos
from nu._config.branding import BLUE, PURPLE


if TYPE_CHECKING:
    from pathlib import Path


_console = Console()


def _description(path: Path) -> str:
    """Return the first line of the module docstring, or empty string."""
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except (OSError, SyntaxError):
        return ""
    doc = ast.get_docstring(tree) or ""
    return doc.strip().splitlines()[0] if doc else ""


def _list(found: dict[str, Path]) -> None:
    if not found:
        _console.print("[yellow]no demos found[/yellow]")
        sys.exit(1)
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style=f"bold {BLUE}")
    table.add_column(style="dim")
    for name, path in found.items():
        table.add_row(name, _description(path))
    _console.print(Text("demos", style=f"bold {PURPLE}"))
    _console.print(table)
    _console.print(Text.assemble(("run with: ", "dim"), ("nu demo <name>", f"bold {BLUE}")))


@click.command(help="List bundled demos, or run one by name (nu demo <name>).")
@click.argument("name", required=False)
def demo(name: str | None) -> None:
    """No arg -> list; name -> run that demo."""
    found = demos()
    if name is None:
        _list(found)
        return
    if name not in found:
        _console.print(f"[red]unknown demo:[/red] [bold]{name}[/bold]", highlight=False)
        _console.print(
            Text.assemble(
                ("available: ", "dim"),
                (", ".join(found) or "(none)", BLUE),
            ),
        )
        sys.exit(2)
    try:
        runpy.run_path(str(found[name]), run_name="__main__")
    except KeyboardInterrupt:
        # Ctrl+C during a demo: nudle already printed its stopped banner;
        # don't let click surface its default "Aborted!" line on top of it.
        pass
