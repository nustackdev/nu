"""`nu doctor` — report python + which fabric extras resolve."""

from __future__ import annotations

import importlib.util
import sys

import click

from nu.cli._meta import nu_version


# Fabric extras (as declared in pyproject) and the import that proves they resolve.
_FABRICS: dict[str, str] = {
    "virtuals": "virtuals",
    "mem": "janus",
    "ui": "nudle",
    "ray": "ray",
    "invisibles": "invisibles",
}


@click.command(help="Report installed fabrics and versions.")
def doctor() -> None:
    """Report installed fabrics and versions."""
    click.echo(f"nu {nu_version()}  (python {sys.version.split()[0]})\n")
    click.echo("Fabrics:")
    width = max(len(name) for name in _FABRICS)
    for name, probe in _FABRICS.items():
        if importlib.util.find_spec(probe) is not None:
            click.echo(f"  {name:<{width}}  ok")
        else:
            click.echo(f"  {name:<{width}}  missing  (pip install 'nustack-py[{name}]')")
