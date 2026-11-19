"""bind() and the presets: give an Agent a command to spawn, for the span of a tree."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.fabric import Provide
from nu.lang import Nu

from . import CLAUDE, CODEX, GEMINI, OPENCODE
from .fabric import DEFAULT_PERMISSIONS, PERMISSIONS, AcpFabric
from .refs import agent_name


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .refs import AgentRef


__all__ = ["CLAUDE", "CODEX", "GEMINI", "OPENCODE", "bind", "claude", "codex", "gemini", "opencode"]


def bind(
    agent: AgentRef | str | Nu,
    *,
    command: Sequence[str] | Nu,
    cwd: str | Nu | None = None,
    mcp_servers: Sequence[Mapping[str, object]] | Nu | None = None,
    env: Mapping[str, str] | Nu | None = None,
    permissions: str | Nu = DEFAULT_PERMISSIONS,
) -> Provide:
    """Run any ACP Agent under ``agent``'s name: spawned on enter, stopped on exit.

    Args:
        agent: the Agent the fabric binds under, its ``AgentRef`` or its name.
        command: the Agent's command line, argv style.
        cwd: the default ``cwd`` of new_session, load and resume, and where
            the process starts; the current directory when None. A per-call
            ``cwd`` wins.
        mcp_servers: the default ACP McpServer dicts of new_session, load and
            resume. A per-call list wins, an empty one included.
        env: set for the Agent on top of this process's environment, such as
            an API key.
        permissions: ``"allow_once"``, ``"allow_always"``, ``"reject_once"``
            (the default) or ``"reject_always"`` answers every request
            inside the fabric with the option of that kind, and yields
            nothing. When a request offers no option of that kind, the
            other kind of the same leaning is taken (``allow_once`` for
            ``allow_always`` and back, the same for reject); offering
            neither, the request is answered ``cancelled``. ``"ask"`` yields
            each request through ``prompt`` and ``updates`` and holds the
            turn until ``answer_permission`` runs: opt in only where
            something answers, such as an agent cell, or a reader like
            ``nu.Collect`` waits forever. A request that arrives after
            ``cancel`` or ``close`` is answered ``cancelled`` under any
            policy.

    Notes:
        - Async only: run the tree with ``nu.arun``.
        - Any argument may be a term, such as a slot read from a store: it
          is evaluated when the bracket opens, and its value is checked
          then, by the fabric, the same as a plain one is checked here.
        - The Agent's capabilities gate what is sent: a method, argument or
          Content Block it did not advertise raises ``AcpError`` (-32601)
          before anything goes out.

    Example:
        nu.With(nustd.acp.bind(Goose, command=["goose", "acp"]), body=...)
    """
    if not isinstance(command, Nu) and (isinstance(command, str) or not command):
        raise TypeError(f"command is the Agent's argv, a non-empty list of str, got {command!r}")
    if not isinstance(permissions, Nu) and permissions not in PERMISSIONS:
        raise ValueError(f"permissions is one of {', '.join(PERMISSIONS)}, got {permissions!r}")
    spec = {
        "command": command if isinstance(command, Nu) else [str(part) for part in command],
        "cwd": cwd if cwd is None or isinstance(cwd, Nu) else str(cwd),
        "mcp_servers": (
            mcp_servers
            if mcp_servers is None or isinstance(mcp_servers, Nu)
            else [dict(s) for s in mcp_servers]
        ),
        "env": env if env is None or isinstance(env, Nu) else dict(env),
        "permissions": permissions,
    }
    return Provide(AcpFabric, spec, tag=agent_name(agent))


def claude(
    agent: AgentRef | str | Nu,
    *,
    cwd: str | Nu | None = None,
    mcp_servers: Sequence[Mapping[str, object]] | Nu | None = None,
    env: Mapping[str, str] | Nu | None = None,
    permissions: str | Nu = DEFAULT_PERMISSIONS,
) -> Provide:
    """Claude Code, through the ``claude-agent-acp`` adapter; see ``bind`` for the kwargs.

    Notes:
        - Runs through ``npx``, so Node must be on PATH. The adapter uses the
          machine's Claude login, or ``ANTHROPIC_API_KEY`` passed in ``env``.
    """
    return bind(
        agent, command=CLAUDE, cwd=cwd, mcp_servers=mcp_servers, env=env, permissions=permissions
    )


def codex(
    agent: AgentRef | str | Nu,
    *,
    cwd: str | Nu | None = None,
    mcp_servers: Sequence[Mapping[str, object]] | Nu | None = None,
    env: Mapping[str, str] | Nu | None = None,
    permissions: str | Nu = DEFAULT_PERMISSIONS,
) -> Provide:
    """Codex, through the ``codex-acp`` adapter; see ``bind`` for the kwargs.

    Notes:
        - Runs through ``npx``, so Node must be on PATH. The adapter uses the
          machine's Codex login, or ``OPENAI_API_KEY`` passed in ``env``.
    """
    return bind(
        agent, command=CODEX, cwd=cwd, mcp_servers=mcp_servers, env=env, permissions=permissions
    )


def gemini(
    agent: AgentRef | str | Nu,
    *,
    cwd: str | Nu | None = None,
    mcp_servers: Sequence[Mapping[str, object]] | Nu | None = None,
    env: Mapping[str, str] | Nu | None = None,
    permissions: str | Nu = DEFAULT_PERMISSIONS,
) -> Provide:
    """Gemini CLI, which speaks ACP itself; see ``bind`` for the kwargs."""
    return bind(
        agent, command=GEMINI, cwd=cwd, mcp_servers=mcp_servers, env=env, permissions=permissions
    )


def opencode(
    agent: AgentRef | str | Nu,
    *,
    cwd: str | Nu | None = None,
    mcp_servers: Sequence[Mapping[str, object]] | Nu | None = None,
    env: Mapping[str, str] | Nu | None = None,
    permissions: str | Nu = DEFAULT_PERMISSIONS,
) -> Provide:
    """OpenCode, which speaks ACP itself; see ``bind`` for the kwargs."""
    return bind(
        agent, command=OPENCODE, cwd=cwd, mcp_servers=mcp_servers, env=env, permissions=permissions
    )
