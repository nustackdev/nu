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

from nu.core.flows.strategy import Sequential
from nu.core.spans.bracket import _LifecycleBracket


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Context


__all__ = ["Session", "SessionHandle"]


class SessionHandle:
    """The mutable cell a Session binds, holding the id once a prompt has produced one.

    Empty until the first prompt inside the bracket returns; from then on
    every prompt in the bracket reads the id off it and resumes. Bound in
    the Context under its own type, which is how the compiled prompt thunks
    find it without the Session being their parent.
    """

    __slots__ = ("session_id",)

    def __init__(self) -> None:
        self.session_id: str | None = None


def _wrap_body(children: tuple[Nu, ...]) -> Nu:
    if len(children) == 1:
        return children[0]
    return Sequential(*children)


class Session(_LifecycleBracket):
    """Makes every prompt in its body continue one Claude Code conversation.

    Without it each prompt is a cold start that remembers nothing. The
    bracket binds a fresh handle on entry; the first prompt underneath runs
    without resuming and writes the id cc gave it onto the handle, and each
    later prompt reads it back and resumes, so the agent keeps its context
    across the whole body.

    Args:
        *body: the terms to run inside the session. Several are run in
            order, as if wrapped in ``Sequential``.

    Notes:
        - Reach is by Context, not by ownership: any prompt evaluated
          while the bracket is open joins the session, including ones
          inside functions the body calls.
        - A nested Session binds its own handle and shadows the outer one,
          so its prompts form a separate conversation. Sibling Sessions
          likewise never share.
        - The handle is bound at the same point whether the run is sync or
          async, so the bracket behaves the same under ``nu.run`` and
          ``nu.arun``.
        - Nothing is persisted. The id lives for as long as the bracket is
          open; to pick a conversation back up later, keep the
          ``session_id`` a prompt yielded and pass it as ``resume=``.

    Yields:
        Whatever the body yields; the bracket adds nothing of its own.

    Example:
        class Agent(nu.Service):
            ask = nu.cc.PromptRef.method()
        app = nu.With(
            nu.cc.bind(Agent, model="claude-sonnet-4-5"),
            body=nu.cc.Session(
                nu.print(nu.dict(Agent.ask("pick a number between 1 and 10"))["text"]),
                nu.print(nu.dict(Agent.ask("what number did you pick?"))["text"]),
            ),
        )
        asyncio.run(nu.arun(app))
    """

    def __init__(self, *body: Nu) -> None:
        super().__init__(_wrap_body(body))

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        yield ctx.bind(SessionHandle, SessionHandle())
