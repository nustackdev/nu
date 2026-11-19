"""The ACP interactions: one atom per ACP method, on the Agent or on one of its Sessions.

Slot 0 is the ref the method addresses: an ``AgentRef`` for the agent methods,
a ``SessionRef`` (``agent[session_id]``) for the session ones. Everything else
is a child, so a session id, a prompt or a cwd can come from any term.

====================  ===========================  ============  =======
atom                  ACP                          sort          mutates
====================  ===========================  ============  =======
AcpInitialization     initialize (its response)    ScalarQuery   -
AcpAuthenticate       authenticate                 Command       {0}
AcpLogout             logout                       Command       {0}
AcpNewSession         session/new                  ScalarAction  {0}
AcpListSessions       session/list                 StreamQuery   -
AcpLoad               session/load                 StreamAction  {0}
AcpResume             session/resume               ScalarAction  {0}
AcpPrompt             session/prompt               StreamAction  {0}
AcpCancel             session/cancel               Command       {0}
AcpAnswerPermission   session/request_permission   Command       {0}
AcpSetMode            session/set_mode             Command       {0}
AcpSetConfigOption    session/set_config_option    ScalarAction  {0}
AcpClose              session/close                Command       {0}
AcpDelete             session/delete               Command       {0}
AcpUpdates            session/update               StreamQuery   -
====================  ===========================  ============  =======

A request yields its response, as a snake_case dict. A request the Agent
streams Session Updates through while it is open (prompt, load) is a stream:
the updates, then the response last. Notifications the Client sends are
Commands.

Every atom is async-only: the connection lives on ``nu.arun``'s loop, and
``nu.run`` refuses a tree holding one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarAction, ScalarQuery, StreamAction, StreamQuery

from .core import (
    acompile_agent,
    acompile_session,
    agent_node,
    refused,
    session_node,
)
from .fabric import AcpFabric


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import StrArg


__all__ = [
    "AcpAnswerPermission",
    "AcpAuthenticate",
    "AcpCancel",
    "AcpClose",
    "AcpDelete",
    "AcpInitialization",
    "AcpListSessions",
    "AcpLoad",
    "AcpLogout",
    "AcpNewSession",
    "AcpPrompt",
    "AcpResume",
    "AcpSetConfigOption",
    "AcpSetMode",
    "AcpUpdates",
]


_ASYNC = Declared(value=True, name="requires_async")
_MUTATES_REF = Declared(value=frozenset({0}), name="mutates")


# --- the Agent ------------------------------------------------------------------


class AcpInitialization(ScalarQuery):
    """What the Agent said about itself when the connection opened.

    Args:
        agent: the agent slot, an ``AgentRef``.

    Notes:
        - A read of what setup got, not a request: ``initialize`` runs once,
          when the fabric is entered.

    Yields:
        ``{protocol_version, agent_capabilities, auth_methods, agent_info}``.

    Example:
        nu.Dict(Claude.initialization())["agent_capabilities"]
    """

    _requires_async = _ASYNC

    def __init__(self, agent: object) -> None:
        super().__init__(agent_node(agent))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_agent(children, AcpFabric.initialization)


class AcpAuthenticate(Command):
    """Runs one of the login flows the Agent advertises in ``auth_methods``.

    Args:
        agent: the agent slot, an ``AgentRef``.
        method_id: the ``id`` of an agent-type auth method.

    Notes:
        - The signal to call it is an ``AcpError`` with code -32000 from
          new_session or another auth-gated request.
        - Terminal-type methods are not run this way, and the fabric does not
          advertise terminal login, so Agents do not offer them.

    Example:
        Codex.authenticate("chat-gpt")
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(self, agent: object, method_id: StrArg) -> None:
        super().__init__(agent_node(agent), method_id)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_agent(children, AcpFabric.authenticate)


class AcpLogout(Command):
    """Logs the Agent out.

    Args:
        agent: the agent slot, an ``AgentRef``.

    Notes:
        - Only Agents advertising ``agent_capabilities.auth.logout`` take it.
          What happens to their live Sessions is theirs to decide.
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(self, agent: object) -> None:
        super().__init__(agent_node(agent))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_agent(children, AcpFabric.logout)


class AcpNewSession(ScalarAction):
    """Starts a Session; the Agent mints its id.

    Args:
        agent: the agent slot, an ``AgentRef``.
        cwd: the Session's working directory, fixed for its life. None takes
            the bind's.
        mcp_servers: ACP McpServer dicts the Agent connects to, which is how
            a Client hands it tools. None takes the bind's.
        additional_directories: more roots beside ``cwd``. Agents that
            advertise ``session_capabilities.additional_directories`` take it.
        system_prompt: a ``str`` appended to the Agent's own system prompt,
            or ACP's ``{mode, content}`` dict. An Agent that cannot apply it
            refuses the Session.

    Yields:
        ``{session_id, modes, config_options}``. Keep the id: it is the
        Session's address, ``agent[session_id]``, here and after a restart.

    Example:
        nu.Dict(Claude.new_session(cwd="/srv/repo"))["session_id"]
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(
        self,
        agent: object,
        cwd: StrArg | None = None,
        mcp_servers: object = None,
        additional_directories: object = None,
        system_prompt: object = None,
    ) -> None:
        super().__init__(agent_node(agent), cwd, mcp_servers, additional_directories, system_prompt)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_agent(children, AcpFabric.new_session)


class AcpListSessions(StreamQuery):
    """The Sessions the Agent keeps, every page of them.

    Args:
        agent: the agent slot, an ``AgentRef``.
        cwd: only the Sessions under this working directory; None lists all.

    Notes:
        - Discovery only: a listed Session is not active on the connection
          until ``load`` or ``resume``.
        - Pages are fetched as the stream is pulled, following
          ``next_cursor`` to the end.
        - Agents that advertise ``session_capabilities.list`` take it.

    Yields:
        One ``{session_id, cwd, title, updated_at}`` per Session.

    Example:
        nu.Collect(Claude.list_sessions(cwd="/srv/repo"))
    """

    _requires_async = _ASYNC

    def __init__(self, agent: object, cwd: StrArg | None = None) -> None:
        super().__init__(agent_node(agent), cwd)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_agent(children, AcpFabric.list_sessions)


# --- one Session ---------------------------------------------------------------


class AcpLoad(StreamAction):
    """Restores a Session and replays its whole conversation.

    Args:
        session: the session slot, ``agent[session_id]``.
        cwd: the cwd the Session was made with. None takes the bind's.
        mcp_servers: as for ``new_session``. None takes the bind's.
        additional_directories: the full list again; leaving it out does
            not bring back the Session's old roots.
        system_prompt: the one the Session was made with, as for
            ``new_session``.

    Notes:
        - Agents that advertise ``agent_capabilities.load_session`` take it.
        - Holds the Session like a Prompt Turn does: a prompt asked meanwhile
          waits for the replay to end.

    Yields:
        The replayed Session Updates, then ``{modes, config_options}``.

    Example:
        nu.ForEachDo(Claude[sid].load(), lambda u: Log.append(u))
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(
        self,
        session: object,
        cwd: StrArg | None = None,
        mcp_servers: object = None,
        additional_directories: object = None,
        system_prompt: object = None,
    ) -> None:
        super().__init__(
            session_node(session), cwd, mcp_servers, additional_directories, system_prompt
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.load)


class AcpResume(ScalarAction):
    """Restores a Session without replaying it.

    Args:
        session: the session slot, ``agent[session_id]``.
        cwd: the cwd the Session was made with. None takes the bind's.
        mcp_servers: as for ``new_session``. None takes the bind's.
        additional_directories: as for ``load``.
        system_prompt: as for ``load``.

    Notes:
        - Agents that advertise ``session_capabilities.resume`` take it.

    Yields:
        ``{modes, config_options}``.

    Example:
        Claude[Chat.sid].resume()
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(
        self,
        session: object,
        cwd: StrArg | None = None,
        mcp_servers: object = None,
        additional_directories: object = None,
        system_prompt: object = None,
    ) -> None:
        super().__init__(
            session_node(session), cwd, mcp_servers, additional_directories, system_prompt
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.resume)


class AcpPrompt(StreamAction):
    """One Prompt Turn: everything the Agent does to answer, as it happens.

    Args:
        session: the session slot, ``agent[session_id]``.
        prompt: a ``str``, sent as one text Content Block, or a list of
            Content Block dicts (``text``, ``image``, ``resource_link``,
            ``resource``, ...) as ACP shapes them.

    Notes:
        - Lazy: the turn starts when the first item is pulled.
        - One Prompt Turn at a time per Session: a second prompt waits for
          the first one's stop reason. To interrupt, ``cancel``, then prompt.
        - A reader that lets go early cancels the turn and waits it out, so
          the next prompt finds the Session idle.
        - A turn that fails raises ``AcpError``. A stop reason is not a
          failure: ``cancelled``, ``max_tokens`` and ``refusal`` end the
          stream like ``end_turn`` does.
        - Permission requests are answered by the bind's policy,
          ``reject_once`` unless it says otherwise, and never yielded. Under
          ``permissions="ask"`` each one is yielded and the turn waits until
          ``answer_permission`` (or ``cancel``) runs, from this stream's
          reader or any other arm; a reader that only collects never
          answers, so ask is for trees that do.
        - Image, audio and embedded resource blocks need the Agent's
          ``prompt_capabilities``; without them the term raises before the
          prompt is sent.
        - ``updates()`` readers get the same items, the turn's end included,
          so an arm that folds ``updates()`` can drain this stream unread.

    Yields:
        Session Updates (``{"session_update": ...}``) and permission requests
        (``{"request_permission": id, "tool_call", "options"}``) in the order
        the Agent sent them, then ``{stop_reason}``.

    Example:
        nu.ForEachDo(Claude[sid].prompt("fix the failing test"), lambda u: nu.print(u))
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(self, session: object, prompt: object) -> None:
        super().__init__(session_node(session), prompt)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.prompt)


class AcpCancel(Command):
    """Stops the Session's Prompt Turn.

    Args:
        session: the session slot, ``agent[session_id]``.

    Notes:
        - Never waits for the turn: it is how a running one is stopped.
        - Every permission request still pending on the Session is answered
          ``cancelled``, as ACP requires, and so is any the Agent sends
          until the turn ends.
        - The turn then ends with stop reason ``cancelled``; its prompt
          stream yields whatever the Agent sends until then.

    Example:
        nu.ReactEvery(Ui.stop.on_click(), lambda _: Claude[sid].cancel())
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(self, session: object) -> None:
        super().__init__(session_node(session))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.cancel)


class AcpAnswerPermission(Command):
    """Answers a permission request the Session's turn is waiting on.

    Args:
        session: the session slot, ``agent[session_id]``.
        request: the request's id, its item's ``request_permission``.
        option_id: one of its options' ``option_id``; anything else raises.

    Notes:
        - Runs from any arm, as the turn waits on its own stream.
        - A request already answered, or cancelled, is left alone, so an
          answer racing a ``cancel`` is harmless.
        - The Agent remembers ``allow_always`` and ``reject_always``
          answers itself.

    Example:
        Claude[sid].answer_permission(item["request_permission"], "allow")
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(self, session: object, request: object, option_id: StrArg) -> None:
        super().__init__(session_node(session), request, option_id)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.answer_permission)


class AcpSetMode(Command):
    """Switches the Session to one of its ``modes``.

    Args:
        session: the session slot, ``agent[session_id]``.
        mode_id: an ``id`` from ``modes.available_modes``.

    Notes:
        - ACP prefers config options: an Agent that offers a ``mode``
          category config option is set with ``set_config_option``.
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(self, session: object, mode_id: StrArg) -> None:
        super().__init__(session_node(session), mode_id)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.set_mode)


class AcpSetConfigOption(ScalarAction):
    """Sets one of the Session's config options: its model, mode, effort, ...

    Args:
        session: the session slot, ``agent[session_id]``.
        config_id: the option's ``id``.
        value: one of a select option's values, or a bool for a boolean
            option.

    Yields:
        The complete ``config_options`` list after the change: setting one
        may change others.

    Example:
        Claude[sid].set_config_option("model", "sonnet")
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(self, session: object, config_id: StrArg, value: object) -> None:
        super().__init__(session_node(session), config_id, value)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.set_config_option)


class AcpClose(Command):
    """Ends the Session on this connection; the Agent keeps its history.

    Args:
        session: the session slot, ``agent[session_id]``.

    Notes:
        - Cancels the Session's work first, as ``cancel`` would.
        - A Session that is already gone is no error.
        - Agents that advertise ``session_capabilities.close`` take it.
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(self, session: object) -> None:
        super().__init__(session_node(session))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.close)


class AcpDelete(Command):
    """Removes the Session from the Agent's ``list_sessions``.

    Args:
        session: the session slot, ``agent[session_id]``.

    Notes:
        - Whether the history goes too is the Agent's choice.
        - A Session that is already gone is no error.
        - Agents that advertise ``session_capabilities.delete`` take it.
    """

    _mutates = _MUTATES_REF
    _requires_async = _ASYNC

    def __init__(self, session: object) -> None:
        super().__init__(session_node(session))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.delete)


class AcpUpdates(StreamQuery):
    """Everything the Agent says about the Session from now on, inside a Prompt Turn or not.

    Args:
        session: the session slot, ``agent[session_id]``.

    Notes:
        - Never ends: drain it in an arm of its own, beside the arms that
          prompt.
        - Every reader gets every item; a prompt stream open on the Session
          gets the turn's items too.
        - Each Prompt Turn's end comes in wire order, after the turn's last
          update, so one reader can fold whole turns without the prompt
          stream. A turn the Agent answered with a JSON-RPC error ends with
          ``{"stop_reason": None, "error": AcpError}``; one with no answer
          (the connection gone, or dropped past its wind-down) ends nowhere.
        - Starts listening when the term runs. Items sent before that are
          not replayed.
        - Raises ``AcpError`` if the Agent process dies.

    Yields:
        Session Updates and permission requests, as ``prompt`` yields them,
        and each Prompt Turn's ``{stop_reason}``, the item ``prompt`` yields
        last.

    Example:
        nu.ForEachDo(Claude[sid].updates(), lambda u: Log.append(u))
    """

    _requires_async = _ASYNC

    def __init__(self, session: object) -> None:
        super().__init__(session_node(session))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return refused(self)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_session(children, AcpFabric.updates)
