"""OnAny: one subscription over several."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.core.reactive.protocol import Subscription
    from nu.lang.runtime import Runtime

__all__ = ["OnAny"]


class AnySubscription:
    """A ``Subscription`` over several: every call goes to every member.

    A receiver bound here is bound on each member as is, so it hears every
    member's notifications with their own keys. ``close`` closes every
    member, even when one of them raises, and re-raises the first error.
    """

    def __init__(self, members: tuple[Subscription, ...]) -> None:
        self.members = members

    def bind(self, receiver: Callable) -> None:
        """Bind ``receiver`` on every member.

        A member that refuses the bind unbinds ``receiver`` from the members
        already bound, then the error propagates.
        """
        for i, sub in enumerate(self.members):
            try:
                sub.bind(receiver)
            except BaseException:
                for bound in self.members[:i]:
                    with contextlib.suppress(Exception):
                        bound.unbind(receiver)
                raise

    def unbind(self, receiver: Callable) -> None:
        """Unbind ``receiver`` from every member."""
        for sub in self.members:
            sub.unbind(receiver)

    def close(self) -> None:
        """Close every member; the first error raised is re-raised after all are closed."""
        _close_all(self.members)


def _close_all(subs: tuple[Subscription, ...] | list[Subscription]) -> None:
    """Close each of ``subs``, then re-raise the first error any of them raised."""
    first: Exception | None = None
    for sub in subs:
        try:
            sub.close()
        except Exception as exc:  # every member is closed before the first error surfaces
            if first is None:
                first = exc
    if first is not None:
        raise first


class OnAny(ScalarQuery):
    """Opens every member subscription and yields one ``Subscription`` over all of them.

    The way a flow listens to several sources: a flow takes one ``change``
    child, and ``OnAny`` makes several subscriptions into one.

    Args:
        *subs: the member subscriptions, any source term (``OnChange``,
            ``view.on_change()``, another ``OnAny``, ...). At least one.

    Raises:
        TypeError: at build time, when given no member.

    Notes:
        - Every member is evaluated, in order, each time ``OnAny`` is. A
          member that fails to open closes the ones already open, and its
          error propagates; an error closing them is dropped so it does not
          hide the open failure.
        - ``bind`` and ``unbind`` go to every member with the same receiver,
          so a receiver hears each member's notifications with that
          member's own key. Nothing is merged or deduplicated: two members
          firing for one write are two notifications.
        - ``close`` closes every member.
        - ``OnAny(a)`` behaves as ``a``, and members nest:
          ``OnAny(a, OnAny(b, c))`` behaves as ``OnAny(a, b, c)``.
        - Async only, like every source: the sync path raises
          ``RuntimeError``; use ``nu.arun``.

    Yields:
        One ``Subscription`` over every member.

    Example:
        Re-run a pass when either table moves. Needs a real substrate behind
        the subscriptions, so it cannot run standalone::

            nu.Reconcile(nu.OnAny(users.on_change(), teams.on_change()), sync_members)
    """

    def __init__(self, *subs: object) -> None:
        if not subs:
            msg = "OnAny needs at least one subscription"
            raise TypeError(msg)
        super().__init__(*subs)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            msg = "OnAny requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        del nid

        async def athunk(rt: Runtime) -> AnySubscription:
            opened: list[Subscription] = []
            try:
                for member in children:
                    opened.append(await member(rt))
            except BaseException:
                # The open failure (or cancellation) is what the caller sees:
                # a member failing to close must not replace it.
                with contextlib.suppress(Exception):
                    _close_all(opened)
                raise
            return AnySubscription(tuple(opened))

        return athunk
