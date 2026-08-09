"""Root click group for the `nu` CLI (rendered via rich-click)."""

from __future__ import annotations

import rich_click as click

from nu._branding import BLUE, PURPLE, render_header
from nu._cli._meta import nu_version
from nu._cli.commands.demo import demo
from nu._cli.commands.doctor import doctor
from nu._cli.commands.telemetry import telemetry


# Rich-click styling: strict brand duo -- purple headers, blue values.
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.STYLE_HEADER_TEXT = f"bold {PURPLE}"
click.rich_click.STYLE_USAGE = f"bold {PURPLE}"
click.rich_click.STYLE_SWITCH = f"bold {PURPLE}"
click.rich_click.STYLE_OPTION = f"bold {BLUE}"
click.rich_click.STYLE_COMMAND = f"bold {BLUE}"
click.rich_click.STYLE_METAVAR = BLUE
click.rich_click.STYLE_HELPTEXT_FIRST_LINE = "bold"
click.rich_click.STYLE_HELPTEXT = ""
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.MAX_WIDTH = 100


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Nu: the interaction primitive.",
)
@click.version_option(nu_version(), "-V", "--version", prog_name="nu")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Root `nu` group; individual commands are attached below."""
    if ctx.invoked_subcommand is None:
        render_header()
        click.echo(ctx.get_help())


cli.add_command(demo)
cli.add_command(doctor)
cli.add_command(telemetry)


def main() -> None:
    """Console-script entrypoint for `nu`."""
    cli()
