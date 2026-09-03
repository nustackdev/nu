"""The call form: what a thing is written with.

Neither source is enough on its own. A signature carries names, defaults and
the variadic tail but says nothing about meaning. A docstring carries the
meaning, and for anything on an inherited variadic constructor it is the only
place the real argument list exists at all.

So they are merged here, which is the contract's job rather than either
reader's: the signature wins on structure when it has any, the docstring
supplies the prose, and when the signature has nothing to say the docstring
stands alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.info.core.contract.sections import ARGS
from nu.info.core.docstring import parse_args
from nu.info.core.source import read_signature


if TYPE_CHECKING:
    from nu.info.core.docstring import Blocks


__all__ = [
    "Arg",
    "call_form",
]


@dataclass(frozen=True)
class Arg:
    """One argument, as it is written and as the code declares it."""

    name: str
    text: str = ""
    default: str = ""
    variadic: bool = False


def call_form(target: object, blocks: Blocks) -> tuple[Arg, ...]:
    """The arguments ``target`` is written with, in order.

    Args:
        target: the object being described.
        blocks: its docstring, split.

    Returns:
        One Arg per argument. Empty when neither source says anything, which
        means absent rather than "takes none".
    """
    documented = {arg.name: arg for arg in parse_args(blocks.text_of(*ARGS))}
    signature = read_signature(target)
    if signature is not None and signature.params:
        return tuple(
            Arg(
                name=param.name,
                text=documented[param.name].text if param.name in documented else "",
                default=param.default,
            )
            for param in signature.params
        )
    return tuple(
        Arg(name=arg.name, text=arg.text, variadic=arg.variadic) for arg in documented.values()
    )
