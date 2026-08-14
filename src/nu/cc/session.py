"""Session: lifecycle bracket that scopes a cc session across nested prompts.

Mirrors the nu.kv pattern (Snapshot / Transaction): a lazy handle is bound into
the ctx on entry; every PromptRef call inside the bracket reads it and threads
`resume=session_id` so cc treats the calls as one continuous session.

The first prompt starts a fresh cc session (no resume); its returned session_id
is captured on the handle, and subsequent prompts continue it.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from nu.flows.strategy import Sequential
from nu.spans.bracket import _LifecycleBracket


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Context


__all__ = ["Session", "SessionHandle"]


class SessionHandle:
    """Mutable holder: starts empty, first prompt fills in the session id."""

    __slots__ = ("session_id",)

    def __init__(self) -> None:
        self.session_id: str | None = None


def _wrap_body(children: tuple[Nu, ...]) -> Nu:
    if len(children) == 1:
        return children[0]
    return Sequential(*children)


class Session(_LifecycleBracket):
    """Scopes a cc session across all PromptRef calls in the body.

    Nested Sessions and sibling top-level Sessions each get a fresh handle.
    """

    def __init__(self, *body: Nu) -> None:
        super().__init__(_wrap_body(body))

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        yield ctx.bind(SessionHandle, SessionHandle())
