"""`nu demo` — list and run bundled demos."""

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


@click.group(invoke_without_command=True, help="List or run a bundled demo.")
@click.pass_context
def demo(ctx: click.Context) -> None:
    """List or run a bundled demo."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_)


@demo.command("list", help="List available demos with a one-line description.")
def list_() -> None:
    """List available demos with a one-line description."""
    found = demos()
    if not found:
        click.echo("no demos found")
        sys.exit(1)
    width = max(len(n) for n in found)
    click.echo("demos:")
    for name, path in found.items():
        click.echo(f"  {click.style(name.ljust(width), bold=True)}  {_description(path)}")
    click.echo("\nrun with: nu demo run <name>")


@demo.command("run", help="Run a demo by name.")
@click.argument("name")
def run(name: str) -> None:
    """Run a demo by name."""
    found = demos()
    if name not in found:
        click.echo(f"unknown demo: {name}", err=True)
        click.echo(f"available: {', '.join(found) or '(none)'}", err=True)
        sys.exit(2)
    runpy.run_path(str(found[name]), run_name="__main__")
