"""Shared compile thunks: resolve the agent or session slot, await the rest, call the fabric."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from nu.lang import Nu
from nu.lang.null import is_null

from .fabric import AcpFabric


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "acompile_agent",
    "acompile_session",
    "agent_node",
    "fabric_of",
    "refused",
    "session_node",
    "session_of",
]


def agent_node(agent: object) -> Nu:
    """The agent slot, a term such as an ``AgentRef``; anything else is refused."""
    if not isinstance(agent, Nu):
        msg = (
            f"the agent slot is a term, such as an AgentRef, got {agent!r}: "
            "build acp terms from the agent, as agent.new_session()"
        )
        raise TypeError(msg)
    return agent


def session_node(session: object) -> Nu:
    """The session slot, a ``SessionRef``; anything else is refused."""
    if not isinstance(session, Nu):
        msg = (
            f"the session slot is a term, such as agent[session_id], got {session!r}: "
            "build session terms from it, as agent[session_id].prompt(text)"
        )
        raise TypeError(msg)
    return session


def fabric_of(value: object) -> AcpFabric:
    """The fabric behind the agent slot's value; NULL means nothing was bound."""
    if is_null(value) or value is None:
        hint = f" for {value.hint}" if is_null(value) and value.hint else ""
        msg = (
            f"no ACP agent is bound{hint}: wrap the tree in "
            "nu.With(nustd.acp.claude(agent, ...), body=...) or nustd.acp.bind(agent, command=[...])"
        )
        raise RuntimeError(msg)
    if not isinstance(value, AcpFabric):
        raise TypeError(f"the agent slot yielded {type(value).__name__}, not an AcpFabric")
    return value


def session_of(value: object) -> tuple[AcpFabric, str]:
    """The fabric and the session id a ``SessionRef`` read yields."""
    if is_null(value) or value is None:
        fabric_of(value)
    fabric, session_id = value  # type: ignore[misc]
    if is_null(session_id) or not isinstance(session_id, str) or not session_id:
        msg = (
            f"a session id is a non-empty str, got {session_id!r}: "
            "take it from new_session()'s session_id"
        )
        raise ValueError(msg)
    return fabric_of(fabric), session_id


def _given(value: object) -> object:
    """A child that may be left out: NULL reads as None."""
    return None if is_null(value) else value


def refused(term: object) -> Callable:
    """The sync thunk of every acp atom: refuses to run."""
    name = type(term).__name__

    def thunk(rt: Runtime) -> None:
        raise RuntimeError(f"{name}: nustd.acp is async-only; use nu.arun")

    return thunk


async def _settled(result: object) -> object:
    """A scalar call is awaited; a stream call hands back its async iterator untouched."""
    return await result if inspect.isawaitable(result) else result


def acompile_agent(children: tuple[Callable, ...], call: Callable) -> Callable:
    """Async compile for an atom on an ``AgentRef``: ``call(fabric, *values)``."""
    agent, *rest = children

    async def athunk(rt: Runtime) -> object:
        fabric = fabric_of(await agent(rt))
        values = [_given(await child(rt)) for child in rest]
        return await _settled(call(fabric, *values))

    return athunk


def acompile_session(children: tuple[Callable, ...], call: Callable) -> Callable:
    """Async compile for an atom on a ``SessionRef``: ``call(fabric, session_id, *values)``."""
    session, *rest = children

    async def athunk(rt: Runtime) -> object:
        fabric, session_id = session_of(await session(rt))
        values = [_given(await child(rt)) for child in rest]
        return await _settled(call(fabric, session_id, *values))

    return athunk
