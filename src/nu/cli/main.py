"""Root click group for the `nu` CLI."""

from __future__ import annotations

import click

from nu.cli._meta import nu_version
from nu.cli.commands.demo import demo
from nu.cli.commands.doctor import doctor
from nu.cli.commands.telemetry import telemetry


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Nu: the interaction primitive.",
)
@click.version_option(nu_version(), "-V", "--version", prog_name="nu")
def cli() -> None:
    """Root `nu` group; individual commands are attached below."""


cli.add_command(demo)
cli.add_command(doctor)
cli.add_command(telemetry)


def main() -> None:
    """Console-script entrypoint for `nu`."""
    cli()
