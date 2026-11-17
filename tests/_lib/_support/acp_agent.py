"""A scripted ACP v1 Agent for the ``nustd.acp`` tests, run as a real subprocess.

    python acp_agent.py

The prompt's text picks what a turn does:

- ``hello``: two ``agent_message_chunk`` pieces, ``hel`` and ``lo``, then ``end_turn``.
- ``perm``: a ``tool_call``, a permission request (allow / always / reject), then a
  chunk saying the outcome (``selected:<option>`` or ``cancelled``); ``cancelled``
  as the stop reason if the turn was cancelled meanwhile.
- ``perm-reject``: the same, offering only a ``reject_once`` option.
- ``wait``: a ``waiting`` chunk, then holds the turn until ``session/cancel``,
  then a ``stopped`` chunk and ``cancelled``.
- ``slow``: sleeps 0.2s, then ``end_turn``.
- ``probe``: a chunk with how many prompts were running on the Session as it began.
- ``later``: ``end_turn``, then 50ms after the response a ``session_info_update``.
- ``client``: calls ``fs/read_text_file``, ``terminal/create`` and an extension on the
  Client, then a chunk with the JSON-RPC error code each got.
- ``late``: a ``go`` chunk, then 0.2s later a permission request, then a chunk with
  its outcome; a cancel sent on ``go`` crosses the request on the wire.
- ``stubborn``: an ``ignoring`` chunk, then holds the turn through any cancel.
- ``orphan``: starts a child that inherits stdout, says ``orphan:<pid>``, then exits
  with code 3 while the child holds the pipe open.
- ``die``: a ``dying`` chunk, then the process exits with code 3.
- ``stats``: a chunk with this Agent's record as JSON (cancels, modes, auth, ...).

Sessions are minted ``s1``, ``s2``, ...; ``old`` exists from the start with a
two message history and is not active until loaded or resumed. ``list`` pages
five stored Sessions two at a time. ``FAKE_ACP_VERSION`` sets the protocol
version ``initialize`` answers with; ``FAKE_ACP_BARE`` makes it advertise no
capabilities at all; ``FAKE_ACP_STDERR_KB`` writes that many KiB to
stderr before serving.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from typing import Any

from acp import RequestError, run_agent


CONFIG = [
    {
        "id": "model",
        "name": "Model",
        "category": "model",
        "type": "select",
        "currentValue": "small",
        "options": [{"value": "small", "name": "Small"}, {"value": "large", "name": "Large"}],
    },
    {"id": "fast", "name": "Fast", "type": "boolean", "currentValue": False},
]

CAPABILITIES = {
    "loadSession": True,
    "promptCapabilities": {"image": True, "embeddedContext": True},
    "mcpCapabilities": {"http": True},
    "sessionCapabilities": {
        "list": {},
        "resume": {},
        "close": {},
        "delete": {},
        "additionalDirectories": {},
        "systemPrompt": {},
    },
    "auth": {"logout": {}},
}

MODES = {
    "currentModeId": "default",
    "availableModes": [{"id": "default", "name": "Default"}, {"id": "plan", "name": "Plan"}],
}


def chunk(text: str) -> dict[str, Any]:
    return {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": text}}


class FakeAgent:
    def __init__(self) -> None:
        self.conn: Any = None
        self.minted = 0
        self.active: set[str] = set()
        self.stored = {f"k{i}": f"/w/{i}" for i in range(5)}
        self.history = {"old": ["what is 2+2", "4"]}
        self.running: dict[str, int] = {}
        self.cancelled: dict[str, asyncio.Event] = {}
        self.record: dict[str, Any] = {"cancels": {}, "modes": {}, "auth": [], "logout": 0}
        self.config = json.loads(json.dumps(CONFIG))

    def on_connect(self, conn: Any) -> None:
        self.conn = conn

    def observe(self, event: Any) -> None:
        """Keep the raw params of every session/new, as the wire had them."""
        message = event.message
        if event.direction.value == "incoming" and message.get("method") == "session/new":
            self.record.setdefault("raw_new", []).append(message.get("params"))

    async def send(self, session_id: str, update: dict[str, Any]) -> None:
        await self.conn._conn.send_notification(
            "session/update", {"sessionId": session_id, "update": update}
        )

    def require(self, session_id: str) -> None:
        if session_id not in self.active:
            raise RequestError(-32002, "Resource not found", {"sessionId": session_id})

    async def initialize(self, protocol_version: int, **kwargs: Any) -> dict[str, Any]:
        return {
            "protocolVersion": int(os.environ.get("FAKE_ACP_VERSION", "1")),
            "agentCapabilities": {} if os.environ.get("FAKE_ACP_BARE") else CAPABILITIES,
            "authMethods": [{"id": "key", "name": "API key"}],
            "agentInfo": {"name": "fake", "version": "1.0"},
        }

    async def authenticate(self, method_id: str, **kwargs: Any) -> dict[str, Any]:
        self.record["auth"].append(method_id)
        return {}

    async def logout(self, **kwargs: Any) -> dict[str, Any]:
        self.record["logout"] += 1
        return {}

    async def new_session(self, cwd: str, **kwargs: Any) -> dict[str, Any]:
        self.minted += 1
        session_id = f"s{self.minted}"
        self.active.add(session_id)
        self.record.setdefault("cwd", {})[session_id] = cwd
        servers = kwargs.get("mcp_servers") or []
        self.record.setdefault("mcp", {})[session_id] = [s.name for s in servers]
        return {"sessionId": session_id, "modes": MODES, "configOptions": self.config}

    async def load_session(self, cwd: str, session_id: str, **kwargs: Any) -> dict[str, Any]:
        if session_id not in self.history:
            raise RequestError(-32002, "Resource not found", {"sessionId": session_id})
        user, agent = self.history[session_id]
        await self.send(
            session_id,
            {"sessionUpdate": "user_message_chunk", "content": {"type": "text", "text": user}},
        )
        await self.send(session_id, chunk(agent))
        self.active.add(session_id)
        return {"modes": MODES}

    async def resume_session(self, session_id: str, cwd: str, **kwargs: Any) -> dict[str, Any]:
        if session_id not in self.history:
            raise RequestError(-32002, "Resource not found", {"sessionId": session_id})
        self.active.add(session_id)
        return {"configOptions": self.config}

    async def list_sessions(self, cwd: str | None = None, cursor: str | None = None, **kwargs: Any):
        ids = sorted(self.stored)
        start = int(cursor or 0)
        page = [
            {"sessionId": i, "cwd": self.stored[i], "title": f"t-{i}"}
            for i in ids[start : start + 2]
            if cwd is None or self.stored[i] == cwd
        ]
        result: dict[str, Any] = {"sessions": page}
        if start + 2 < len(ids):
            result["nextCursor"] = str(start + 2)
        return result

    async def close_session(self, session_id: str, **kwargs: Any) -> dict[str, Any]:
        self.require(session_id)
        self.active.discard(session_id)
        return {}

    async def delete_session(self, session_id: str, **kwargs: Any) -> dict[str, Any]:
        if session_id not in self.stored:
            raise RequestError(-32002, "Resource not found", {"sessionId": session_id})
        del self.stored[session_id]
        return {}

    async def set_session_mode(self, session_id: str, mode_id: str, **kwargs: Any) -> dict:
        self.require(session_id)
        self.record["modes"][session_id] = mode_id
        return {}

    async def set_config_option(
        self, config_id: str, session_id: str, value: str | bool, **kwargs: Any
    ) -> dict[str, Any]:
        self.require(session_id)
        for option in self.config:
            if option["id"] == config_id:
                option["currentValue"] = value
                return {"configOptions": self.config}
        raise RequestError.invalid_params({"configId": config_id})

    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        cancels = self.record["cancels"]
        cancels[session_id] = cancels.get(session_id, 0) + 1
        if session_id in self.cancelled:
            self.cancelled[session_id].set()

    async def prompt(self, session_id: str, prompt: list[Any], **kwargs: Any) -> dict[str, Any]:
        self.require(session_id)
        text = " ".join(getattr(block, "text", "") for block in prompt)
        self.running[session_id] = self.running.get(session_id, 0) + 1
        self.cancelled[session_id] = asyncio.Event()
        try:
            return await self.turn(session_id, text)
        finally:
            self.running[session_id] -= 1

    async def turn(self, session_id: str, text: str) -> dict[str, Any]:
        stop = self.cancelled[session_id]
        if text == "hello":
            await self.send(session_id, chunk("hel"))
            await self.send(session_id, chunk("lo"))
        elif text in ("perm", "perm-reject"):
            await self.send(
                session_id,
                {
                    "sessionUpdate": "tool_call",
                    "toolCallId": "t1",
                    "title": "Edit a.py",
                    "kind": "edit",
                    "status": "pending",
                },
            )
            options = [{"optionId": "reject", "name": "Reject", "kind": "reject_once"}]
            if text == "perm":
                options = [
                    {"optionId": "allow", "name": "Allow", "kind": "allow_once"},
                    {"optionId": "always", "name": "Always", "kind": "allow_always"},
                    *options,
                ]
            answer = await self.conn._conn.send_request(
                "session/request_permission",
                {"sessionId": session_id, "toolCall": {"toolCallId": "t1"}, "options": options},
            )
            outcome = answer["outcome"]
            said = outcome["outcome"]
            if said == "selected":
                said = f"selected:{outcome['optionId']}"
            await self.send(session_id, chunk(said))
            if stop.is_set():
                return {"stopReason": "cancelled"}
        elif text == "wait":
            await self.send(session_id, chunk("waiting"))
            await stop.wait()
            await self.send(session_id, chunk("stopped"))
            return {"stopReason": "cancelled"}
        elif text == "slow":
            await asyncio.sleep(0.2)
        elif text == "probe":
            await self.send(session_id, chunk(str(self.running[session_id])))
        elif text == "later":
            asyncio.get_running_loop().call_later(
                0.05,
                lambda: asyncio.ensure_future(
                    self.send(session_id, {"sessionUpdate": "session_info_update", "title": "t"})
                ),
            )
        elif text == "client":
            codes = {}
            for method, params in (
                ("fs/read_text_file", {"path": "/a"}),
                ("terminal/create", {"command": "ls"}),
                ("_x/ping", {}),
            ):
                try:
                    await self.conn._conn.send_request(method, {"sessionId": session_id, **params})
                    codes[method] = "answered"
                except RequestError as exc:
                    codes[method] = exc.code
            await self.send(session_id, chunk(json.dumps(codes)))
        elif text == "late":
            # The client's cancel crosses this request on the wire.
            await self.send(session_id, chunk("go"))
            await asyncio.sleep(0.2)
            answer = await self.conn._conn.send_request(
                "session/request_permission",
                {
                    "sessionId": session_id,
                    "toolCall": {"toolCallId": "t9"},
                    "options": [{"optionId": "allow", "name": "Allow", "kind": "allow_once"}],
                },
            )
            await self.send(session_id, chunk(answer["outcome"]["outcome"]))
            return {"stopReason": "cancelled" if stop.is_set() else "end_turn"}
        elif text == "stubborn":
            # Ignores session/cancel; only $/cancel_request stops it.
            await self.send(session_id, chunk("ignoring"))
            await asyncio.sleep(30)
        elif text == "orphan":
            # A child that keeps the Agent's stdout open after the Agent is gone.
            child = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(30)"], stdin=subprocess.DEVNULL
            )
            await self.send(session_id, chunk(f"orphan:{child.pid}"))
            await asyncio.sleep(0.05)
            os._exit(3)
        elif text == "die":
            await self.send(session_id, chunk("dying"))
            await asyncio.sleep(0.05)
            os._exit(3)
        elif text == "stats":
            await self.send(session_id, chunk(json.dumps(self.record)))
        return {"stopReason": "end_turn"}


if __name__ == "__main__":
    # A chatty Agent: more stderr than a pipe holds, before it says a word on stdout.
    for _ in range(int(os.environ.get("FAKE_ACP_STDERR_KB", "0"))):
        sys.stderr.write("x" * 1023 + "\n")
    sys.stderr.flush()
    agent = FakeAgent()
    asyncio.run(run_agent(agent, observers=[agent.observe]))
