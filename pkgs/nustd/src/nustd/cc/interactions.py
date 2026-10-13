"""CCPrompt runs one Claude Code prompt turn, CCStream streams one; NewSession mints the id of a conversation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarAction, ScalarQuery, StreamAction

from .core import (
    acompile_call,
    acompile_new_session,
    acompile_stream,
    compile_call,
    compile_new_session,
    compile_stream,
)


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ["CCPrompt", "CCStream", "NewSession"]


class CCPrompt(ScalarAction):
    """One prompt turn against the Claude Code agent a PromptRef addresses.

    Built by calling a PromptRef rather than written by hand. At evaluation
    it resolves the Ref, merges the endpoint's declared defaults under this
    call's overrides, and drives one ``query`` through the ``CCFabric``
    provided for the owning Service, draining the message stream to the end.

    A whole agent run happens inside this one node: the agent may read
    files, run tools and take many turns before the stream closes. Only the
    final text and the run's accounting come back out.

    Args:
        ref: the PromptRef naming the agent.
        args: a Dict carrying ``prompt`` plus this call's option overrides.

    Notes:
        - Declared as mutating its Ref child, so runs against one agent stay
          ordered and are never folded together.
        - Outside a ``nustd.cc.Session`` it is one-shot: a ``claude`` process
          for this prompt alone, which ``resume=`` can point at an earlier
          conversation. Inside one it is a turn of the brace's conversation,
          and on the async path a turn on the brace's one process.
        - The sync path drives the async SDK through ``asyncio.run``, so it
          raises if a loop is already running. Use ``nu.arun`` anywhere near
          an event loop.

    Yields:
        A dict with ``text`` plus the run's accounting: ``session_id``,
        ``total_cost_usd``, ``duration_ms``, ``num_turns`` and the raw
        ``result``. ``text`` is the SDK's final result string, falling back
        to the concatenated assistant text blocks. If the stream ends
        without a result message the accounting keys are absent entirely,
        not None.

    Example:
        class Agent(nu.Service):
            ask = nustd.cc.PromptRef.method()
        app = nu.With(
            nustd.cc.bind(Agent, model="claude-sonnet-4-5", permission_mode="acceptEdits"),
            body=nu.print(nu.dict(Agent.ask("write a haiku about rust"))["text"]),
        )
        asyncio.run(nu.arun(app))
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)


class CCStream(StreamAction):
    """One prompt turn against a Claude Code agent, its reply streamed as it happens.

    Built by calling a StreamRef rather than written by hand. It runs the
    turn a ``CCPrompt`` runs, through the same fabric and the same Session,
    but where that one hands back only the end, this one yields each thing
    the agent does the moment it lands: its text, its tool calls and what
    they gave back, then the result with the run's accounting.

    Args:
        ref: the StreamRef naming the agent.
        args: a Dict carrying ``prompt`` plus this call's option overrides.

    Notes:
        - Lazy, as every stream is: nothing starts until something pulls the
          first event, and a reader that stops early stops the run. Inside a
          Session that also closes the brace's process, since the rest of the
          reply is left unread on it; the next prompt opens a new one on the
          same conversation.
        - Inside a Session the turn holds the brace's process until its
          result is out, so other prompts in the brace wait for it.
        - Text arrives a block at a time. Bind ``include_partial_messages=True``
          to also get ``delta`` events, pieces of a block as it is written.
        - The sync path pulls the async SDK through a thread of its own, so
          events still arrive as they happen under ``nu.run``.

    Yields:
        One dict per event, keyed by ``type``:

        - ``init``: ``session_id``, ``model``, ``cwd``, ``tools``.
        - ``text`` / ``thinking``: ``text``, a whole block.
        - ``delta``: ``text``, a piece of a block (partial messages only).
        - ``tool_use``: ``id``, ``name``, ``input``.
        - ``tool_result``: ``id`` (the tool_use's), ``content`` as text cut to
          ``nustd.cc.fabric.TRIM`` characters, ``is_error``.
        - ``result``, always last: ``text``, ``session_id``,
          ``total_cost_usd``, ``duration_ms``, ``num_turns``, ``usage``,
          ``is_error``. A stream that ends without one carries no result.

    Example:
        class Agent(nu.Service):
            say = nustd.cc.StreamRef.method()
        app = nu.With(
            nustd.cc.bind(Agent, model="claude-sonnet-5"),
            body=nu.ForEachDo(Agent.say("list this directory"), lambda ev: nu.print(ev["type"])),
        )
        asyncio.run(nu.arun(app))
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_stream(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_stream(children)


class NewSession(ScalarQuery):
    """A new conversation id, for a ``nustd.cc.Session`` to begin under.

    The CLI lets a caller choose the id of a conversation, so creating one is
    minting a UUID and nothing else: no process starts and nothing is written.
    The conversation begins on the first prompt in a Session given this id,
    and every later Session given it continues it. So the id can be stored
    before anything is said, and whoever holds it can pick the conversation
    back up after a restart.

    Notes:
        - A Query that reads randomness, as ``nustd.uuid.uuid4`` is: every
          evaluation is a new id, and nothing is mutated.

    Yields:
        The id, a str.

    Example:
        app = nu.With(
            nustd.cc.bind(Agent),
            body=nu.let(
                nustd.cc.NewSession(),
                lambda sid: nustd.cc.Session(Agent.ask("hello"), sid=sid),
            ),
        )
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_new_session(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_new_session(children)
