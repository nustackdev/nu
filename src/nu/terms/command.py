"""Command, ScalarCommand.

A Command yields nothing and contributes ≥1 WRITE through its
`own_effects`. The class-time validator enforces that requirement on
concrete `Command` subclasses.

ScalarCommand is the operand-driven shape: open each child, take its
first value, call `run` / `arun`. The native pair is `run` / `arun`.
"""

from __future__ import annotations

from typing import Any

from .interaction import Interaction
from .nu import register_subclass_validator
from .types import Effect


__all__ = [
    "Command",
    "ScalarCommand",
]


class Command(Interaction):
    """Abstract Command base. ≥1 slot in `own_effects` carries WRITE."""


class ScalarCommand(Command):
    """Operand-driven Command. Native pair: `run` / `arun`.

    Concrete subclasses override `run` / `arun`. The stream-fed
    behaviour (existing ExitStack-based child suspension across the
    WRITE) lives in the runtime path that Phase D wires; declarations
    here are stubs.
    """

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        msg = f"{type(self).__name__}.run - phase D"
        raise NotImplementedError(msg)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        msg = f"{type(self).__name__}.arun - phase D"
        raise NotImplementedError(msg)


def _validate_command(cls: type) -> None:
    """Concrete Command subclasses must declare ≥1 WRITE in own_effects.

    Abstract subclasses (e.g. ScalarCommand itself) are exempt - they
    don't ship `own_effects` of their own.
    """
    if cls.__name__ == "ScalarCommand":
        return
    if "own_effects" not in cls.__dict__:
        # An intermediate abstract base. Skip; concrete leaves will check.
        return
    own = cls.__dict__["own_effects"]
    has_write = False
    for eff in own.values():
        effs = eff if isinstance(eff, frozenset) else {eff}
        if Effect.WRITE in effs:
            has_write = True
            break
    if not has_write:
        msg = (
            f"{cls.__module__}.{cls.__qualname__}: Command kinds must "
            "declare at least one WRITE slot in own_effects."
        )
        raise TypeError(msg)


register_subclass_validator(Command, _validate_command)
