"""CCPrompt: ScalarAction that runs one Claude Code prompt turn."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarAction

from .core import acompile_call, compile_call


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ["CCPrompt"]


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
        - Under a ``nu.cc.Session`` bracket it reads the session id off the
          handle and resumes; the first call in the bracket starts fresh and
          writes its id back for the rest.
        - An explicit ``resume=`` override wins over the bracket's handle.
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
            ask = nu.cc.PromptRef.method()
        app = nu.With(
            nu.cc.bind(Agent, model="claude-sonnet-4-5", permission_mode="acceptEdits"),
            body=nu.print(nu.dict(Agent.ask("write a haiku about rust"))["text"]),
        )
        asyncio.run(nu.arun(app))
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)
