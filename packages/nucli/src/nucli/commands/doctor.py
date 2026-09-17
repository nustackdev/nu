"""`nu doctor` — report python + which fabric extras resolve."""

from __future__ import annotations

import importlib.util
import sys

import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from nu._config.branding import BLUE, PURPLE
from nucli._meta import nu_version


# Fabric extras (as declared in packages/nustd/pyproject.toml) and the imports
# that prove they resolve. The backends live in the `nustd` distribution; this
# kernel-side command only probes for them, it never imports the fabric.
#
# Everything an extra imports at module scope belongs here, or the row goes
# green on an install that cannot import. `ui` reaches `nudle` lazily, from the
# static mount, and it is probed anyway: without it the browser gets no bundle.
_FABRICS: dict[str, tuple[str, ...]] = {
    "kv": ("virtuals",),
    "mem": ("janus",),
    "ui": ("fastapi", "uvicorn", "msgpack", "watchfiles", "nudle"),
    "cluster": ("ray",),
    "proxy": ("invisibles",),
    "http": ("httpx",),
    "llm": ("httpx",),
    "cc": ("claude_agent_sdk",),
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
    for name, probes in _FABRICS.items():
        if all(importlib.util.find_spec(probe) is not None for probe in probes):
            table.add_row(name, Text("● ok", style="green"), "")
        else:
            table.add_row(
                name,
                Text("○ missing", style="yellow"),
                # Text, not a bare str: rich reads `[ui]` in a plain string as
                # a style tag and eats it, leaving "pip install 'nustd'".
                Text(f"pip install 'nustd[{name}]'"),
            )
    console.print(table)
