"""`nu telemetry` — inspect and toggle the anonymous usage ping."""

from __future__ import annotations

import rich_click as click
from rich.console import Console
from rich.text import Text

from nu._branding import BLUE
from nu._config import config as _config


_console = Console()


def _state_line(on: bool) -> Text:
    label = Text("telemetry: ", style="dim")
    label.append("on" if on else "off", style="bold green" if on else "bold yellow")
    return label


@click.group(invoke_without_command=True, help="Anonymous usage telemetry.")
@click.pass_context
def telemetry(ctx: click.Context) -> None:
    """`nu telemetry` — default action shows current status."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(status)


@telemetry.command("status", help="Show current telemetry state.")
def status() -> None:
    """Print on/off, distinct_id, and config path."""
    on = _config.telemetry_enabled()
    dev = _config.is_dev_install()
    _console.print(_state_line(on))
    if dev:
        _console.print("[dim]dev install detected — no events sent regardless[/dim]")
    _console.print(Text.assemble(("distinct_id: ", "dim"), (_config.distinct_id(), BLUE)))
    _console.print(Text.assemble(("config:      ", "dim"), (str(_config.CONFIG_PATH), BLUE)))


@telemetry.command("enable", help="Turn telemetry on.")
def enable() -> None:
    """Set the config flag to on."""
    _config.set_telemetry(True)
    _console.print(_state_line(True))


@telemetry.command("disable", help="Turn telemetry off.")
def disable() -> None:
    """Set the config flag to off."""
    _config.set_telemetry(False)
    _console.print(_state_line(False))
