"""Nu ACP fabric: coding agents (Claude Code, Codex, Gemini, OpenCode, ...) over ACP v1.

The fabric is the ACP Client. The refs are the Agent and its Sessions, and
each ACP method is one interaction. Fields keep ACP's names, snake_cased as
the Python SDK has them.

Surface:
    - AgentRef(name): an Agent; its terms are ``initialization``,
      ``authenticate``, ``logout``, ``new_session`` and ``list_sessions``,
      and ``agent[session_id]`` is one of its Sessions.
    - SessionRef: a Session; its terms are ``load``, ``resume``, ``prompt``,
      ``cancel``, ``answer_permission``, ``set_mode``, ``set_config_option``,
      ``close``, ``delete`` and ``updates``.
    - claude, codex, gemini, opencode: bind an Agent by its usual command;
      bind(agent, command=[...]) binds any other.
    - AcpFabric: the Agent process and the connection to it, beneath them all.
    - AcpError: a JSON-RPC error from the Agent, or a lost connection.
    - AcpPrompt, AcpUpdates, ...: the interactions those terms build.

``prompt`` streams a Prompt Turn: Session Updates (``{"session_update": ...}``)
as the Agent sends them, then ``{"stop_reason": ...}``. Permission requests
are answered by the bind's policy (``reject_once`` by default); under
``permissions="ask"`` they are yielded too (``{"request_permission": id,
...}``) and wait for ``answer_permission``. ``updates`` yields the same
items, each turn's ``{"stop_reason": ...}`` included, in and out of turns.
Async only: run with ``nu.arun``.

Example::

    Claude = nustd.acp.AgentRef("claude")

    app = nu.With(
        nustd.acp.claude(Claude, cwd="/srv/repo"),
        body=nu.let(
            lambda sid: nu.ForEachDo(Claude[sid].prompt("why does test_kv flake?"), nu.print),
            sid=nu.Dict(Claude.new_session())["session_id"],
        ),
    )

    asyncio.run(nu.arun(app))
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .fabric import PERMISSIONS, AcpError, AcpFabric
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
    from .presets import bind, claude, codex, gemini, opencode
    from .refs import AgentRef, SessionRef


#: The commands the presets spawn. Plain data, so a program can name an Agent's
#: command without the ACP SDK installed.
CLAUDE = ("npx", "-y", "@agentclientprotocol/claude-agent-acp")
CODEX = ("npx", "-y", "@agentclientprotocol/codex-acp")
GEMINI = ("gemini", "--acp")
OPENCODE = ("opencode", "acp")


# Everything else here stands on the ACP SDK, so it loads on first access, and a
# missing SDK is named as the extra that brings it.
_LAZY = {
    "AcpAnswerPermission": "interactions",
    "AcpAuthenticate": "interactions",
    "AcpCancel": "interactions",
    "AcpClose": "interactions",
    "AcpDelete": "interactions",
    "AcpError": "fabric",
    "AcpFabric": "fabric",
    "AcpInitialization": "interactions",
    "AcpListSessions": "interactions",
    "AcpLoad": "interactions",
    "AcpLogout": "interactions",
    "AcpNewSession": "interactions",
    "AcpPrompt": "interactions",
    "AcpResume": "interactions",
    "AcpSetConfigOption": "interactions",
    "AcpSetMode": "interactions",
    "AcpUpdates": "interactions",
    "AgentRef": "refs",
    "PERMISSIONS": "fabric",
    "SessionRef": "refs",
    "bind": "presets",
    "claude": "presets",
    "codex": "presets",
    "gemini": "presets",
    "opencode": "presets",
}


def __getattr__(name: str) -> object:
    """Load a name on first access."""
    if name not in _LAZY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        module = importlib.import_module(f".{_LAZY[name]}", __name__)
    except ModuleNotFoundError as exc:
        if exc.name != "acp" and not (exc.name or "").startswith("acp."):
            raise
        msg = "nustd.acp requires the ACP SDK: pip install nustd[acp]"
        raise AttributeError(msg) from exc
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *_LAZY})


__all__ = [
    "CLAUDE",
    "CODEX",
    "GEMINI",
    "OPENCODE",
    "PERMISSIONS",
    "AcpAnswerPermission",
    "AcpAuthenticate",
    "AcpCancel",
    "AcpClose",
    "AcpDelete",
    "AcpError",
    "AcpFabric",
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
    "AgentRef",
    "SessionRef",
    "bind",
    "claude",
    "codex",
    "gemini",
    "opencode",
]
