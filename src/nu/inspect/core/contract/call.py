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
    from nu.inspect.core.docstring import Blocks, DocArg
    from nu.inspect.core.source import Param, Signature


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

    ``variadic`` marks the ``*args`` tail and ``keyword_variadic`` the
    ``**kw`` tail. ``name`` is always the bare name, without the stars.
    """

    name: str
    text: str = ""
    default: str = ""
    variadic: bool = False
    keyword_variadic: bool = False
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
    if signature is not None and _signature_speaks(target, signature, documented):
        return _from_signature(signature, documented)
    return tuple(
        Arg(
            name=arg.name,
            text=arg.text,
            variadic=arg.variadic,
            keyword_variadic=arg.keyword_variadic,
        )
        for arg in documented.values()
    )


def _signature_speaks(target: object, signature: Signature, documented: dict[str, DocArg]) -> bool:
    """Whether the signature has anything to say about how ``target`` is written.

    Named parameters always do. A signature that is only tails, ``(*args,
    **kw)``, is the inherited pass-through constructor on a class, whose real
    argument list lives in the docstring, so a class falls back to the
    docstring. On a function or method the tails are the real list,
    ``method(**defaults)``, unless the docstring names arguments the tails do
    not, which means the tails are a pass-through there too.
    """
    if signature.params:
        return True
    if isinstance(target, type) or not (signature.variadic or signature.keyword_variadic):
        return False
    tails = {signature.variadic_name, signature.keyword_variadic_name} - {""}
    return set(documented) <= tails


def _from_signature(signature: Signature, documented: dict[str, DocArg]) -> tuple[Arg, ...]:
    """The signature's arguments in the order they are written, prose merged in.

    Positional parameters, then ``*args``, then keyword-only ones, then
    ``**kw``: the tails are part of how the callable is written, so they are
    kept even though nothing binds to them by name.
    """

    def text(name: str) -> str:
        return documented[name].text if name in documented else ""

    def named(param: Param) -> Arg:
        return Arg(
            name=param.name,
            text=text(param.name),
            default=param.default,
            annotation=param.annotation,
            keyword_only=param.keyword_only,
            has_default=param.has_default,
        )

    args = [named(param) for param in signature.positional]
    if signature.variadic:
        args.append(
            Arg(name=signature.variadic_name, text=text(signature.variadic_name), variadic=True)
        )
    args.extend(named(param) for param in signature.keyword)
    if signature.keyword_variadic:
        name = signature.keyword_variadic_name
        args.append(Arg(name=name, text=text(name), keyword_only=True, keyword_variadic=True))
    return tuple(args)


def render_args(name: str, args: tuple[Arg, ...]) -> str:
    """A call form: ``name(a, b=default, *rest, **kw)``.

    The one place a call form is spelled, so every kind's record agrees on it
    and no consumer reassembles one from the arguments itself.
    """
    return f"{name}({', '.join(_render(arg) for arg in args)})"


def _render(arg: Arg) -> str:
    if arg.keyword_variadic:
        return f"**{arg.name}"
    if arg.variadic:
        return f"*{arg.name}"
    return f"{arg.name}={arg.default}" if arg.has_default else arg.name
