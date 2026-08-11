"""`nu doctor` — report python + which fabric extras resolve."""

from __future__ import annotations

import importlib.util
import sys

import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from nu._branding import BLUE, PURPLE
from nu._cli._meta import nu_version


# Fabric extras (as declared in pyproject) and the import that proves they resolve.
_FABRICS: dict[str, str] = {
    "kv": "virtuals",
    "mem": "janus",
    "ui": "nudle",
    "ray": "ray",
    "invisibles": "invisibles",
}


@click.command(help="Report installed fabrics and versions.")
def doctor() -> None:
    """Report installed fabrics and versions."""
    console = Console()
    header = Text.assemble(
        ("nu ", f"bold {PURPLE}"),
        (nu_version(), f"bold {BLUE}"),
        ("  ·  python ", "dim"),
        (sys.version.split()[0], BLUE),
    )
    console.print(header)
    console.print()
    table = Table(show_header=True, header_style=f"bold {PURPLE}", box=None, padding=(0, 2))
    table.add_column("fabric", style="bold")
    table.add_column("status")
    table.add_column("install", style="dim")
    for name, probe in _FABRICS.items():
        if importlib.util.find_spec(probe) is not None:
            table.add_row(name, Text("● ok", style="green"), "")
        else:
            table.add_row(
                name,
                Text("○ missing", style="yellow"),
                f"pip install 'nustack-py[{name}]'",
            )
    console.print(table)
