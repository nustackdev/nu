import rich_click as click

from .commands.remote import remote as remote_command
from .commands.ui import ui as ui_command


@click.group()
@click.option("-v", "--verbose", is_flag=True)
def loomix(verbose):
    if verbose:
        click.echo("Verbose mode is on")


loomix.add_command(ui_command, "ui")
loomix.add_command(remote_command, "remote")


if __name__ == "__main__":
    loomix()
