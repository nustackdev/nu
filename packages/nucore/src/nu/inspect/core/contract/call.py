"""The call form: what a thing is written with.

Neither source is enough on its own. A signature carries names, defaults and
the variadic tail but says nothing about meaning. A docstring carries the
meaning, and for anything on an inherited variadic constructor it is the only
place the real argument list exists at all.

So they are merged here, which is the contract's job rather than either
reader's: the signature wins on structure when it has any, the docstring
supplies the prose, and when the signature has nothing to say the docstring
stands alone.

Rendering the merged arguments back into the string a person writes is here
too, for the same reason: an atom whose arguments exist only in its docstring
still has a call form, so the renderer has to run off the merge rather than
off either source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.inspect.core.contract.sections import ARGS
from nu.inspect.core.docstring import parse_args
from nu.inspect.core.source import read_signature


if TYPE_CHECKING:
    from nu.inspect.core.docstring import Blocks


__all__ = [
    "Arg",
    "call_form",
    "render_args",
]


@dataclass(frozen=True)
class Arg:
    """One argument, as it is written and as the code declares it.

    ``default`` is only meaningful when ``has_default`` is set: an argument
    defaulting to the empty string and one with no default at all are both
    ``default=""``, and only the flag separates them. ``annotation`` and
    ``keyword_only`` come from the signature and are empty and False for an
    argument the docstring is the only source for.
    """

    name: str
    text: str = ""
    default: str = ""
    variadic: bool = False
    annotation: str = ""
    keyword_only: bool = False
    has_default: bool = False


def call_form(target: object, blocks: Blocks, *, receiver: bool = False) -> tuple[Arg, ...]:
    """The arguments ``target`` is written with, in order.

    Args:
        target: the object being described.
        blocks: its docstring, split.
        receiver: whether ``target`` is an unbound method, whose leading
            ``self`` is the receiver and not an argument anybody writes.

    Returns:
        One Arg per argument. Empty when neither source says anything, which
        means absent rather than "takes none".
    """
    documented = {arg.name: arg for arg in parse_args(blocks.text_of(*ARGS))}
    signature = read_signature(target, receiver=receiver)
    if signature is not None and signature.params:
        return tuple(
            Arg(
                name=param.name,
                text=documented[param.name].text if param.name in documented else "",
                default=param.default,
                annotation=param.annotation,
                keyword_only=param.keyword_only,
                has_default=param.has_default,
            )
            for param in signature.params
        )
    return tuple(
        Arg(name=arg.name, text=arg.text, variadic=arg.variadic) for arg in documented.values()
    )


def render_args(name: str, args: tuple[Arg, ...]) -> str:
    """A call form: ``name(a, b=default, *rest)``.

    The one place a call form is spelled, so every kind's record agrees on it
    and no consumer reassembles one from the arguments itself.
    """
    return f"{name}({', '.join(_render(arg) for arg in args)})"


def _render(arg: Arg) -> str:
    if arg.variadic:
        return f"*{arg.name}"
    return f"{arg.name}={arg.default}" if arg.has_default else arg.name
