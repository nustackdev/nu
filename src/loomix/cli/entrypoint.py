import rich_click as click

from .commands import ui


@click.group()
def loomix():
    pass


loomix.add_command(ui)


if __name__ == "__main__":
    loomix()
