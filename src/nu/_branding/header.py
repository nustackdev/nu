"""Shared Nu header: logo on the left, tagline + version + urls on the right.

Used by the CLI (`nu` with no args) and the nudle server banner -- one
shared visual identity across every user-facing entrypoint.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from rich.console import Console
from rich.table import Table
from rich.text import Text

from .logo import logo
from .palette import BLUE


TAGLINE = "The interaction primitive"
DOCS_URL = "https://nustack.dev"
GITHUB_URL = "https://github.com/nustackdev/nu"


def _nu_version() -> str:
    try:
        return version("nustack-py")
    except PackageNotFoundError:
        return "0.0.0+dev"


def _side() -> Text:
    side = Text()
    side.append(TAGLINE)
    side.append("\n")
    side.append(f"v{_nu_version()}", style=f"bold {BLUE}")
    side.append("\n\n")
    side.append(DOCS_URL, style=f"{BLUE} underline")
    side.append("\n\n")
    side.append(GITHUB_URL, style=f"{BLUE} underline")
    return side


def render_header(console: Console | None = None) -> None:
    """Print the shared Nu header: logo on the left, labels on the right."""
    console = console or Console()
    layout = Table.grid(padding=(0, 4))
    layout.add_column()
    layout.add_column(vertical="middle")
    layout.add_row(logo(), _side())
    console.print()
    console.print(layout)
    console.print()
