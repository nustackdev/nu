"""AgentRef and SessionRef: the Agent, by the name its fabric binds under, and one of its Sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu.context import FabricRef
from nu.lang import Nu, Ref, ScalarQuery
from nu.lang.null import Null, is_null

from .fabric import AcpFabric
from .interactions import (
    AcpAnswerPermission,
    AcpAuthenticate,
    AcpCancel,
    AcpClose,
    AcpDelete,
    AcpInitialization,
    AcpListSessions,
    AcpLoad,
    AcpLogout,
    AcpNewSession,
    AcpPrompt,
    AcpResume,
    AcpSetConfigOption,
    AcpSetMode,
    AcpUpdates,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.forms import Iterator
    from nu.forms.primitives import Bool
    from nu.lang import StrArg
    from nu.lang.runtime import Runtime


__all__ = ["AgentRef", "SessionRef", "agent_name"]


def agent_name(agent: object) -> str | Nu:
    """The agent's name: an ``AgentRef``'s name term, a non-empty ``str``, or a term computing it.

    A term is returned as given, never looked into; its value is checked when it
    is evaluated.
    """
    if isinstance(agent, AgentRef):
        return agent.name
    if isinstance(agent, Nu):
        return agent
    if isinstance(agent, str) and agent:
        return agent
    raise TypeError(f"an ACP agent is an AgentRef or its name, a non-empty str, got {agent!r}")


class AgentRef(FabricRef):
    """An ACP Agent: the ``AcpFabric`` bound under its name, and the terms that reach it.

    The name is the tag a preset binds under, so several Agents live in one
    tree without meeting. Every term holds this ref itself, so one
    ``AgentRef`` held in a module serves any number of terms and trees.

    Args:
        name: the Agent's name, any non-empty ``str``, or a term yielding
            one, evaluated each time the ref is read.

    Notes:
        - Reading it is a lookup and nothing else: the bound ``AcpFabric``,
          or NULL when nothing is bound under the name.
        - ``agent[session_id]`` addresses one of its Sessions; the id may be
          any term, such as a kv slot holding it.

    Yields:
        The bound ``AcpFabric``, or NULL when nothing is bound for the name.

    Example:
        Claude = nustd.acp.AgentRef("claude")

        app = nu.With(
            nustd.acp.claude(Claude, cwd="/srv/repo"),
            body=nu.let(
                lambda sid: nu.ForEachDo(Claude[sid].prompt("hi"), nu.print),
                sid=nu.Dict(Claude.new_session())["session_id"],
            ),
        )
    """

    fabric = AcpFabric

    def __init__(self, name: str | Nu) -> None:
        # Children: [fabric, name]. A plain name is checked here, a computed
        # one each time it is evaluated.
        super().__init__(None, agent_name(name))

    @property
    def name(self) -> Nu:
        """The Agent's name, the tag its fabric binds under: the name child, a term."""
        return self._children[1]

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric, name_of = children[0], children[1]

        def thunk(rt: Runtime) -> object:
            f = fabric(rt)
            name = cast("str", agent_name(name_of(rt)))
            if rt.ctx.has(f, name):
                return rt.ctx.get(f, name)
            return Null(name)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric, name_of = children[0], children[1]

        async def athunk(rt: Runtime) -> object:
            f = await fabric(rt)
            name = cast("str", agent_name(await name_of(rt)))
            if rt.ctx.has(f, name):
                return rt.ctx.get(f, name)
            return Null(name)

        return athunk

    def __getitem__(self, session_id: StrArg) -> SessionRef:
        """One of the Agent's Sessions, by the id ``new_session`` gave."""
        return SessionRef(self, session_id)

    # --- terms --------------------------------------------------------------

    def initialization(self) -> AcpInitialization:
        """What the Agent said about itself at setup; see ``AcpInitialization``."""
        return AcpInitialization(self)

    def authenticate(self, method_id: StrArg) -> AcpAuthenticate:
        """Run one of the Agent's ``auth_methods``; see ``AcpAuthenticate``."""
        return AcpAuthenticate(self, method_id)

    def logout(self) -> AcpLogout:
        """Log the Agent out."""
        return AcpLogout(self)

    def new_session(
        self,
        *,
        cwd: StrArg | None = None,
        mcp_servers: object = None,
        additional_directories: object = None,
        system_prompt: object = None,
    ) -> AcpNewSession:
        """Start a Session and yield ``{session_id, modes, config_options}``; see ``AcpNewSession``.

        Args:
            cwd: None takes the bind's.
            mcp_servers: None takes the bind's.
            additional_directories: more roots beside ``cwd``.
            system_prompt: a ``str`` to append, or ACP's ``{mode, content}``.
        """
        return AcpNewSession(self, cwd, mcp_servers, additional_directories, system_prompt)

    def list_sessions(self, *, cwd: StrArg | None = None) -> Iterator:
        """Every Session the Agent keeps, one dict each; see ``AcpListSessions``.

        Args:
            cwd: only those under this directory; None lists all.
        """
        from nu.forms import Iterator

        return Iterator(AcpListSessions(self, cwd))

    def exists(self) -> Bool:
        """Whether a fabric is bound under this Agent's name, as a ``Bool``.

        Notes:
            - Overrides the base check, which looks only at the untagged
              binding: an Agent's fabric is always bound under its name.
        """
        from nu.forms.primitives import Bool

        return Bool(_AgentBound(self))


class SessionRef(Ref):
    """One Session of an Agent, ``agent[session_id]``, and the terms that reach it.

    Args:
        agent: the ``AgentRef``.
        session_id: the id, any term: a literal, a let, a kv slot.

    Notes:
        - A Session is usable on the connection after ``new_session``,
          ``load`` or ``resume``, as in ACP; before that the Agent answers
          -32002 and the term raises ``AcpError``.
        - Every term holds this ref itself, so one ``SessionRef`` can be
          held and reused across terms and trees.

    Yields:
        ``(fabric, session_id)``, or NULL when nothing is bound for the
        Agent.

    Example:
        s = Claude[Chat.sid]
        nu.Sequential(s.resume(), nu.Last(s.prompt("where were we?")))
    """

    def __init__(self, agent: AgentRef, session_id: StrArg) -> None:
        if not isinstance(agent, AgentRef):
            raise TypeError(f"a SessionRef hangs off an AgentRef, got {agent!r}")
        super().__init__(agent, session_id)

    @property
    def agent(self) -> AgentRef:
        """The Agent this Session belongs to."""
        return self._children[0]  # type: ignore[return-value]

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        agent, session_id = children

        def thunk(rt: Runtime) -> object:
            fabric = agent(rt)
            return fabric if is_null(fabric) else (fabric, session_id(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        agent, session_id = children

        async def athunk(rt: Runtime) -> object:
            fabric = await agent(rt)
            return fabric if is_null(fabric) else (fabric, await session_id(rt))

        return athunk

    # --- terms --------------------------------------------------------------

    def load(
        self,
        *,
        cwd: StrArg | None = None,
        mcp_servers: object = None,
        additional_directories: object = None,
        system_prompt: object = None,
    ) -> Iterator:
        """Restore the Session: its replayed updates, then ``{modes, config_options}``; see ``AcpLoad``."""
        from nu.forms import Iterator

        return Iterator(AcpLoad(self, cwd, mcp_servers, additional_directories, system_prompt))

    def resume(
        self,
        *,
        cwd: StrArg | None = None,
        mcp_servers: object = None,
        additional_directories: object = None,
        system_prompt: object = None,
    ) -> AcpResume:
        """Restore the Session without a replay; see ``AcpResume``."""
        return AcpResume(self, cwd, mcp_servers, additional_directories, system_prompt)

    def prompt(self, prompt: object) -> Iterator:
        """One Prompt Turn, streamed; see ``AcpPrompt``.

        Args:
            prompt: a ``str``, or a list of ACP Content Block dicts.
        """
        from nu.forms import Iterator

        return Iterator(AcpPrompt(self, prompt))

    def cancel(self) -> AcpCancel:
        """Stop the running Prompt Turn; pending permission requests are answered ``cancelled``."""
        return AcpCancel(self)

    def answer_permission(self, request: object, option_id: StrArg) -> AcpAnswerPermission:
        """Answer the permission request ``request`` with ``option_id``; see ``AcpAnswerPermission``."""
        return AcpAnswerPermission(self, request, option_id)

    def set_mode(self, mode_id: StrArg) -> AcpSetMode:
        """Switch the Session's mode."""
        return AcpSetMode(self, mode_id)

    def set_config_option(self, config_id: StrArg, value: object) -> AcpSetConfigOption:
        """Set one config option and yield the complete ``config_options``."""
        return AcpSetConfigOption(self, config_id, value)

    def close(self) -> AcpClose:
        """End the Session on this connection; the Agent keeps its history."""
        return AcpClose(self)

    def delete(self) -> AcpDelete:
        """Remove the Session from the Agent's list."""
        return AcpDelete(self)

    def updates(self) -> Iterator:
        """Everything the Agent says about the Session from now on; see ``AcpUpdates``."""
        from nu.forms import Iterator

        return Iterator(AcpUpdates(self))


class _AgentBound(ScalarQuery):
    """Whether its ``AgentRef`` reads a bound fabric rather than NULL.

    Yields:
        True or False.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref,) = children

        def thunk(rt: Runtime) -> bool:
            return not is_null(ref(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref,) = children

        async def athunk(rt: Runtime) -> bool:
            return not is_null(await ref(rt))

        return athunk
