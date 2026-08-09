"""`nu telemetry` — inspect and toggle the anonymous usage ping."""

from __future__ import annotations

import click

from nu._config import config as _config


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
    click.echo(f"telemetry: {click.style('on' if on else 'off', bold=True)}")
    if dev:
        click.echo("dev install detected — no events sent regardless")
    click.echo(f"distinct_id: {_config.distinct_id()}")
    click.echo(f"config: {_config.CONFIG_PATH}")


@telemetry.command("enable", help="Turn telemetry on.")
def enable() -> None:
    """Set the config flag to on."""
    _config.set_telemetry(True)
    click.echo("telemetry: on")


@telemetry.command("disable", help="Turn telemetry off.")
def disable() -> None:
    """Set the config flag to off."""
    _config.set_telemetry(False)
    click.echo("telemetry: off")
