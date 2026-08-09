"""`nu demo` — list bundled demos, or run one by name."""

from __future__ import annotations

import ast
import runpy
import sys
from typing import TYPE_CHECKING

import click

from nu.cli._meta import demos


if TYPE_CHECKING:
    from pathlib import Path


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
        click.echo("no demos found")
        sys.exit(1)
    width = max(len(n) for n in found)
    click.echo("demos:")
    for name, path in found.items():
        click.echo(f"  {click.style(name.ljust(width), bold=True)}  {_description(path)}")
    click.echo("\nrun with: nu demo <name>")


@click.command(help="List bundled demos, or run one by name (nu demo <name>).")
@click.argument("name", required=False)
def demo(name: str | None) -> None:
    """No arg -> list; name -> run that demo."""
    found = demos()
    if name is None:
        _list(found)
        return
    if name not in found:
        click.echo(f"unknown demo: {name}", err=True)
        click.echo(f"available: {', '.join(found) or '(none)'}", err=True)
        sys.exit(2)
    runpy.run_path(str(found[name]), run_name="__main__")
