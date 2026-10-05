"""Session: the brace that makes every prompt inside it one Claude Code conversation.

Mirrors the nustd.kv pattern (Snapshot / Transaction): a handle is bound into the
ctx on entry, and every PromptRef call inside the brace finds it there and runs
through it. The handle carries the conversation's id and, on the async path, the
one ``claude`` process the brace talks through.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, Any

from nu.core.flows import Noop
from nu.core.flows.strategy import Sequential
from nu.core.spans.bracket import _aguard, _guard
from nu.lang import Attr, Bracket, Cardinality


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    from nu.lang import Nu, StrArg
    from nu.lang.runtime import Context, Runtime

    from .fabric import CCFabric


__all__ = ["Session", "SessionHandle"]


class SessionHandle:
    """One brace's conversation: its id, and the process it talks through.

    Bound in the Context under its own type, which is how the compiled prompt
    thunks find it without the Session being their parent. The id is the one
    the brace was given, or empty until the first prompt of a fresh brace
    returns one. The client is opened by the first async prompt and closed by
    the brace; a turn that fails closes it too, so the next prompt opens a new
    process on the same id rather than reading a reply cut off halfway.
    """

    __slots__ = ("client", "lock", "options", "sid")

    def __init__(self, sid: str | None) -> None:
        self.sid = sid
        self.client: ClaudeSDKClient | None = None
        self.options: ClaudeAgentOptions | None = None
        self.lock = asyncio.Lock()

    def prompt(self, fabric: CCFabric, prompt: str, overrides: dict[str, object]) -> dict[str, Any]:
        """One prompt on the sync path: a process of its own, on this conversation's id."""
        result = asyncio.run(fabric.aprompt(prompt, sid=self.sid, **overrides))
        self.sid = result.get("session_id") or self.sid
        return result

    async def aprompt(
        self, fabric: CCFabric, prompt: str, overrides: dict[str, object]
    ) -> dict[str, Any]:
        """One prompt on the async path: a turn on the brace's one open process.

        Turns take the lock one at a time, because one process answers one
        prompt at a time and its replies arrive on one stream.
        """
        options = fabric.options_for(overrides)
        async with self.lock:
            if self.client is None:
                self.client = await fabric.aconnect(options, self.sid)
                self.options = options
            elif options != self.options:
                msg = (
                    "a Session runs one claude process, opened with the options of its first "
                    "prompt; this prompt asks for different ones"
                )
                raise ValueError(msg)
            try:
                result = await fabric.aturn(self.client, prompt)
            except BaseException:
                await self.aclose()
                raise
            self.sid = result.get("session_id") or self.sid
            return result

    async def aclose(self) -> None:
        """Close the process if one is open. Safe to call twice."""
        client, self.client = self.client, None
        if client is not None:
            await client.disconnect()


def _wrap_body(children: tuple[Nu, ...]) -> Nu:
    if len(children) == 1:
        return children[0]
    return Sequential(*children)


def _sid_of(value: object) -> str:
    """The id a brace was given, as the CLI wants it. Anything that is not a UUID raises."""
    return str(uuid.UUID(str(value)))


class Session(Bracket):
    """Makes every prompt in its body continue one Claude Code conversation.

    Without it each prompt is a cold start that remembers nothing. With it
    the prompts underneath are turns of one conversation, and on the async
    path they are turns on one ``claude`` process, started by the first
    prompt and stopped when the body ends, fails or is cancelled.

    Args:
        *body: the terms to run inside the session. Several are run in
            order, as if wrapped in ``Sequential``.
        sid: the conversation to be in, a UUID. A conversation that already
            has a transcript is continued; an id that was never prompted
            starts its conversation under that id on the first prompt, so an
            id from ``NewSession`` can be stored before anything is said.
            Without one the brace starts fresh, and the id it ends up with is
            the ``session_id`` of any prompt result inside it.

    Notes:
        - Reach is by Context, not by ownership: any prompt evaluated
          while the brace is open joins the session, including ones
          inside functions the body calls.
        - A nested Session binds its own handle and shadows the outer one,
          so its prompts form a separate conversation. Sibling Sessions
          likewise never share, unless they are given the same ``sid``.
        - One brace is one process, opened with the options of its first
          prompt. A later prompt asking for different options raises,
          including one through a Service bound differently.
        - Prompts inside run one at a time even if the body runs them in
          parallel, because one process answers one prompt at a time.
        - The sync path cannot keep a process open between prompts, since
          each one is its own ``asyncio.run``. There every prompt is a
          process of its own, run on the brace's id, so the conversation is
          the same and only the cost of starting differs.
        - The brace owns the id: a ``resume`` or ``session_id`` override on
          a prompt inside it is replaced. Those overrides are for prompts
          outside any brace.

    Yields:
        Whatever the body yields; the brace adds nothing of its own.

    Example:
        class Agent(nu.Service):
            ask = nustd.cc.PromptRef.method()
        app = nu.With(
            nustd.cc.bind(Agent, model="claude-sonnet-4-5"),
            body=nu.let(
                nustd.cc.NewSession(),
                lambda sid: nustd.cc.Session(
                    nu.print(nu.dict(Agent.ask("pick a number between 1 and 10"))["text"]),
                    nu.print(nu.dict(Agent.ask("what number did you pick?"))["text"]),
                    sid=sid,
                ),
            ),
        )
        asyncio.run(nu.arun(app))
    """

    def __init__(self, *body: Nu, sid: StrArg | None = None) -> None:
        super().__init__(_wrap_body(body), Noop() if sid is None else sid)

    def _sid(self, children: tuple[Callable, ...]) -> Callable | None:
        return None if isinstance(self._children[1], Noop) else children[1]

    @contextmanager
    def _bound(self, ctx: Context, handle: SessionHandle) -> Iterator[None]:
        with ctx.fabrics.bind(SessionHandle, handle):
            yield

    @asynccontextmanager
    async def _abound(self, ctx: Context, handle: SessionHandle) -> AsyncIterator[None]:
        try:
            with ctx.fabrics.bind(SessionHandle, handle):
                yield
        finally:
            await handle.aclose()

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, sid = children[0], self._sid(children)

        def thunk(rt: Runtime) -> object:
            handle = SessionHandle(None if sid is None else _sid_of(sid(rt)))

            def scope(ctx: Context) -> Iterator[None]:
                return self._bound(ctx, handle)

            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _guard(rt, scope, body)
            with scope(rt.ctx):
                return body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, sid = children[0], self._sid(children)

        async def athunk(rt: Runtime) -> object:
            handle = SessionHandle(None if sid is None else _sid_of(await sid(rt)))

            def ascope(ctx: Context) -> AsyncIterator[None]:
                return self._abound(ctx, handle)

            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _aguard(rt, ascope, body)
            async with ascope(rt.ctx):
                return await body(rt)

        return athunk
