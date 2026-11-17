"""AcpFabric: the ACP Client. Spawns one Agent, speaks ACP v1 to it, and routes what it sends."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from collections import deque
from contextlib import AsyncExitStack
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from acp import RequestError, spawn_agent_process
from acp.schema import (
    AllowedOutcome,
    ClientCapabilities,
    DeniedOutcome,
    Implementation,
    InitializeRequest,
    InitializeResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    NewSessionRequest,
    NewSessionResponse,
    RequestPermissionResponse,
    ResumeSessionRequest,
    ResumeSessionResponse,
    TextContentBlock,
)


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence

    from acp.core import ClientSideConnection
    from pydantic import BaseModel

    from nu.lang.runtime import Context


__all__ = [
    "DEFAULT_PERMISSIONS",
    "PERMISSIONS",
    "PROTOCOL_VERSION",
    "WIND_DOWN",
    "AcpError",
    "AcpFabric",
]


log = logging.getLogger("nustd.acp")

T = TypeVar("T")
M = TypeVar("M", bound="BaseModel")

#: The one ACP version the fabric speaks.
PROTOCOL_VERSION = 1

#: What a bind may set ``permissions`` to: ask, or answer every request with the option of a kind.
PERMISSIONS = ("ask", "allow_once", "allow_always", "reject_once", "reject_always")

#: The policy a bind gets unless it says otherwise: a reader that never answers cannot stall a turn.
DEFAULT_PERMISSIONS = "reject_once"

#: Seconds between looks at whether the Agent process has exited.
EXIT_POLL = 0.1

#: Seconds a turn let go of early is given to end after its cancel, before the request is dropped.
WIND_DOWN = 10.0

# The kind a policy answers with, then the kind of the same leaning it settles for.
_FALLBACK = {
    "allow_once": ("allow_once", "allow_always"),
    "allow_always": ("allow_always", "allow_once"),
    "reject_once": ("reject_once", "reject_always"),
    "reject_always": ("reject_always", "reject_once"),
}

#: Lines of the Agent's stderr kept, to say why it died.
STDERR_TAIL = 20

# JSON-RPC error codes the fabric reads and raises.
_NOT_FOUND = -32002
_NO_METHOD = -32601

# Content Block types a prompt may carry only when the Agent advertises them.
_GATED_BLOCKS = {
    "image": "promptCapabilities.image",
    "audio": "promptCapabilities.audio",
    "resource": "promptCapabilities.embeddedContext",
}

_END = object()


class _Closed:
    """Put on every open stream when the connection goes: ``error`` is None for a clean close."""

    __slots__ = ("error",)

    def __init__(self, error: AcpError | None) -> None:
        self.error = error


class AcpError(RuntimeError):
    """The Agent answered a request with a JSON-RPC error, or the connection to it is gone.

    Attributes:
        method: the ACP method that failed, such as ``session/prompt``.
        code: the JSON-RPC error code; None when the connection itself failed.
        data: the error's ``data``, as the Agent sent it.
    """

    def __init__(
        self, method: str, message: str, *, code: int | None = None, data: object = None
    ) -> None:
        super().__init__(f"{method}: {message}")
        self.method = method
        self.code = code
        self.data = data


class _Pending:
    """A permission request waiting for an answer: the options it offered and the answer's future."""

    __slots__ = ("answer", "option_ids")

    def __init__(self, option_ids: frozenset[str]) -> None:
        self.option_ids = option_ids
        self.answer: asyncio.Future[str | None] = asyncio.get_running_loop().create_future()


class _Session:
    """What the fabric holds for one Session: its listeners, its turn and its open questions."""

    __slots__ = ("cancelled", "lock", "pending", "subscribers", "turn")

    def __init__(self) -> None:
        #: One Prompt Turn (or load replay) at a time on the Session.
        self.lock = asyncio.Lock()
        #: The open prompt or load stream's queue, while one runs.
        self.turn: asyncio.Queue | None = None
        #: One queue per open ``updates()`` stream.
        self.subscribers: set[asyncio.Queue] = set()
        #: Permission requests waiting on ``answer_permission``, by request id.
        self.pending: dict[object, _Pending] = {}
        #: Set by cancel and close until the turn's request ends: a request
        #: crossing the cancel on the wire is answered ``cancelled`` at once.
        self.cancelled = False

    def publish(self, item: object) -> None:
        if self.turn is not None:
            self.turn.put_nowait(item)
        for queue in self.subscribers:
            queue.put_nowait(item)

    def cancel(self) -> None:
        """Answer every pending request ``cancelled``, and every later one until the turn ends."""
        self.cancelled = True
        for pending in self.pending.values():
            if not pending.answer.done():
                pending.answer.set_result(None)


class AcpFabric:
    """One Agent process and the ACP v1 connection to it, open for the span of a ``Provide``.

    The fabric is the ACP Client: it spawns the Agent on enter, sends
    ``initialize`` (protocol version 1, and no fs, terminal or elicitation
    capability, so the Agent runs its tools itself), and stops the process on
    exit. One process serves any number of Sessions, and every interaction on
    them goes through here.

    Args:
        command: the Agent's command line, argv style.
        cwd: the working directory the process starts in, and the default
            ``cwd`` of new_session, load and resume. Made absolute; the
            current directory when None.
        mcp_servers: the default ``mcpServers`` of new_session, load and
            resume, as ACP's McpServer dicts.
        env: put over this process's environment for the Agent. The SDK
            alone passes the Agent only a handful of variables, so the whole
            environment goes, with these on top.
        permissions: a kind (``"reject_once"`` by default) answers every
            permission request with the option of that kind, inside the
            fabric. ``"ask"`` yields each request and waits for
            ``answer_permission``. See ``PERMISSIONS``.

    Notes:
        - Async only: the connection lives on the event loop of ``nu.arun``.
        - One instance is shared by every arm of a parallel tree. Sessions
          are independent; on one Session a single Prompt Turn runs at a
          time.
        - A request the Agent makes that the fabric does not implement (fs,
          terminal, elicitation, extensions) is refused with -32601, never
          answered with an empty result.
        - A method, argument or Content Block gated by a capability the
          Agent did not advertise is refused before it is sent, as
          ``AcpError`` code -32601 naming the capability.
    """

    _nu_async_only = True

    def __init__(
        self,
        *,
        command: Sequence[str],
        cwd: str | None = None,
        mcp_servers: Sequence[Mapping[str, object]] | None = None,
        env: Mapping[str, str] | None = None,
        permissions: str = DEFAULT_PERMISSIONS,
    ) -> None:
        if not command:
            raise ValueError("an ACP agent needs a command to spawn it, got an empty one")
        if permissions not in PERMISSIONS:
            raise ValueError(f"permissions is one of {', '.join(PERMISSIONS)}, got {permissions!r}")
        self.command = [str(part) for part in command]
        self.cwd = str(Path(cwd or Path.cwd()).absolute())
        self.mcp_servers = [dict(server) for server in mcp_servers or ()]
        self.env = dict(env or {})
        self.permissions = permissions
        self._stack: AsyncExitStack | None = None
        self._conn: ClientSideConnection | None = None
        self._init: dict[str, Any] = {}
        #: ``agentCapabilities`` as the Agent sent it, camelCase, every field kept.
        self._capabilities: dict[str, Any] = {}
        self._sessions: dict[str, _Session] = {}
        self._stderr: deque[str] = deque(maxlen=STDERR_TAIL)
        self._watchers: list[asyncio.Task] = []
        self._proc: asyncio.subprocess.Process | None = None
        self._closing = False
        #: Why the connection died on its own, once it has.
        self._lost: str | None = None
        self._minted = 0

    # --- lifecycle ----------------------------------------------------------

    async def asetup(self, ctx: Context) -> None:
        """Spawn the Agent and initialize the connection; refuse an Agent that is not on v1."""
        stack = AsyncExitStack()
        try:
            try:
                conn, proc = await stack.enter_async_context(
                    spawn_agent_process(
                        _Client(self),
                        self.command[0],
                        *self.command[1:],
                        env={**os.environ, **self.env},
                        cwd=self.cwd,
                    )
                )
            except OSError as exc:
                raise AcpError("spawn", f"cannot start {self.command[0]!r}: {exc}") from exc
            self._conn = conn
            self._proc = proc
            self._watchers = [
                asyncio.create_task(self._drain(proc.stderr), name="nustd.acp.stderr"),
                asyncio.create_task(self._watch(proc), name="nustd.acp.watch"),
            ]
            # Sent raw: the SDK's typed response drops capabilities newer than
            # its schema (``sessionCapabilities.systemPrompt``), and the fabric
            # gates on all of them.
            request = InitializeRequest(
                protocol_version=PROTOCOL_VERSION,
                client_capabilities=ClientCapabilities(),
                client_info=Implementation(name="nustd.acp", version=_version()),
            )
            raw = await self._rpc(
                "initialize", conn._conn.send_request("initialize", _wire(request))
            )
            response = InitializeResponse.model_validate(raw or {})
            if response.protocol_version != PROTOCOL_VERSION:
                msg = (
                    f"the agent speaks ACP version {response.protocol_version}; "
                    f"nustd.acp speaks version {PROTOCOL_VERSION} only"
                )
                raise AcpError("initialize", msg)
        except BaseException:
            self._closing = True
            await self._stop(stack)
            raise
        self._stack = stack
        self._capabilities = dict((raw or {}).get("agentCapabilities") or {})
        self._init = _response(
            response, "protocol_version", "agent_capabilities", "auth_methods", "agent_info"
        )

    async def acleanup(self) -> None:
        """End every open stream and stop the Agent: stdin closed, then terminate, then kill."""
        self._closing = True
        self._close_streams(None)
        stack, self._stack = self._stack, None
        if stack is not None:
            await self._stop(stack)

    async def _stop(self, stack: AsyncExitStack) -> None:
        try:
            # The SDK signals an Agent that outlived its stdin; one already
            # gone has no process left to signal.
            with contextlib.suppress(ProcessLookupError):
                await stack.aclose()
            # The SDK leaves the process's pipes to close on their own; waiting
            # for that here keeps them from being torn down after this loop is
            # gone. A child holding a pipe open is not waited past a second.
            if self._proc is not None:
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self._proc.wait(), 1.0)
        finally:
            # Once the process is gone its stderr ends; reading to that end
            # closes the pipe on this loop. Whatever is still going after a
            # second (a child holding stderr) is cancelled.
            if self._watchers:
                await asyncio.wait(self._watchers, timeout=1.0)
            for task in self._watchers:
                task.cancel()
            for task in self._watchers:
                with contextlib.suppress(asyncio.CancelledError):
                    await task
            self._watchers = []

    async def _drain(self, stream: asyncio.StreamReader | None) -> None:
        """Read the Agent's stderr as it comes, so a chatty Agent never stalls on a full pipe."""
        if stream is None:
            return
        # Read in pieces, not lines: a line past the reader's limit would raise and stop the drain.
        rest = b""
        while piece := await stream.read(1 << 16):
            *lines, rest = (rest + piece).split(b"\n")
            rest = rest[-(1 << 16) :]
            for line in lines:
                text = line.decode(errors="replace").rstrip()
                self._stderr.append(text)
                log.debug("agent stderr: %s", text)

    async def _watch(self, proc: asyncio.subprocess.Process) -> None:
        """Fail every open stream when the Agent dies on its own."""
        # ``proc.wait()`` also waits for the pipes to close, which a child of
        # the Agent holding its stdout can put off forever; the exit code is
        # known as soon as the process is reaped.
        while proc.returncode is None:
            await asyncio.sleep(EXIT_POLL)
        code = proc.returncode
        if self._closing:
            return
        self._lost = f"the agent exited with code {code}{self._tail()}"
        self._close_streams(AcpError("connection", self._lost))
        # A child of the Agent (npx, node, an MCP server) can hold its stdout
        # open past its death, so the end of the pipe may never come: close
        # the connection now, which fails every request still waiting.
        if self._conn is not None:
            with contextlib.suppress(Exception):
                await self._conn.close()

    def _close_streams(self, error: AcpError | None) -> None:
        closed = _Closed(error)
        for state in self._sessions.values():
            state.publish(closed)

    def _tail(self) -> str:
        if not self._stderr:
            return ""
        return "; its stderr ends with:\n  " + "\n  ".join(self._stderr)

    # --- requests -------------------------------------------------------------

    async def _rpc(self, method: str, call: Awaitable[T]) -> T:
        """Await one request to the Agent, its errors raised as ``AcpError``."""
        try:
            return await call
        except RequestError as exc:
            raise _error(method, exc) from exc
        except ConnectionError as exc:
            reason = self._lost or f"the connection to the agent is closed{self._tail()}"
            raise AcpError(method, reason) from exc

    def _connection(self) -> ClientSideConnection:
        if self._conn is None or self._closing:
            raise RuntimeError("the ACP agent is not running: use it inside the With that binds it")
        return self._conn

    def _state(self, session_id: str) -> _Session:
        state = self._sessions.get(session_id)
        if state is None:
            state = self._sessions[session_id] = _Session()
        return state

    def _require(self, method: str, capability: str) -> None:
        """Refuse ``method`` unless the Agent advertised ``capability``, a dotted camelCase path.

        ACP treats an omitted capability as unsupported, and an object one
        (``{}``) as supported by being there.
        """
        node: object = self._capabilities
        for key in capability.split("."):
            node = node.get(key) if isinstance(node, dict) else None
        if node is None or node is False:
            msg = f"the agent does not advertise agentCapabilities.{capability}"
            raise AcpError(method, msg, code=_NO_METHOD)

    def _require_session_args(
        self,
        method: str,
        mcp_servers: Sequence[Mapping[str, object]],
        additional_directories: object,
        system_prompt: object,
    ) -> None:
        """Gate what new_session, load and resume carry beyond the baseline."""
        for server in mcp_servers:
            kind = server.get("type")
            if kind in ("http", "sse"):
                self._require(method, f"mcpCapabilities.{kind}")
        if additional_directories is not None:
            self._require(method, "sessionCapabilities.additionalDirectories")
        if system_prompt is not None:
            self._require(method, "sessionCapabilities.systemPrompt")
            if _system_prompt(system_prompt).get("mode") == "override":
                self._require(method, "sessionCapabilities.systemPrompt.mode.override")

    def initialization(self) -> dict[str, Any]:
        """The initialize response the Agent gave at setup."""
        self._connection()
        return dict(self._init)

    async def authenticate(self, method_id: str) -> None:
        """Run one of the Agent's advertised ``auth_methods``."""
        conn = self._connection()
        await self._rpc("authenticate", conn.authenticate(method_id=method_id))

    async def logout(self) -> None:
        """Log the Agent out."""
        conn = self._connection()
        self._require("logout", "auth.logout")
        await self._rpc("logout", conn.logout())

    async def new_session(
        self,
        cwd: str | None,
        mcp_servers: Sequence[Mapping[str, object]] | None,
        additional_directories: Sequence[str] | None,
        system_prompt: object,
    ) -> dict[str, Any]:
        """Start a Session; the Agent mints its id."""
        servers = self._mcp(mcp_servers)
        self._require_session_args("session/new", servers, additional_directories, system_prompt)
        request = NewSessionRequest(
            cwd=self._cwd(cwd),
            mcp_servers=servers,
            additional_directories=_listed(additional_directories),
        )
        response = await self._request("session/new", request, NewSessionResponse, system_prompt)
        self._state(response.session_id)
        return _response(response, "session_id", "modes", "config_options")

    async def list_sessions(self, cwd: str | None) -> AsyncIterator[dict[str, Any]]:
        """Every Session the Agent lists, following ``next_cursor`` through all pages."""
        conn = self._connection()
        self._require("session/list", "sessionCapabilities.list")
        cursor = None
        while True:
            page = await self._rpc("session/list", conn.list_sessions(cwd=cwd, cursor=cursor))
            for info in page.sessions:
                yield _response(info, "session_id", "cwd", "title", "updated_at")
            cursor = page.next_cursor
            if not cursor:
                return

    def load(
        self,
        session_id: str,
        cwd: str | None,
        mcp_servers: Sequence[Mapping[str, object]] | None,
        additional_directories: Sequence[str] | None,
        system_prompt: object,
    ) -> AsyncIterator[dict[str, Any]]:
        """Restore a Session: its replayed Session Updates, then the response."""
        self._connection()
        self._require("session/load", "loadSession")
        servers = self._mcp(mcp_servers)
        self._require_session_args("session/load", servers, additional_directories, system_prompt)
        request = LoadSessionRequest(
            session_id=session_id,
            cwd=self._cwd(cwd),
            mcp_servers=servers,
            additional_directories=_listed(additional_directories),
        )
        load = partial(self._request, "session/load", request, LoadSessionResponse, system_prompt)
        return self._turn(session_id, "session/load", load)

    async def resume(
        self,
        session_id: str,
        cwd: str | None,
        mcp_servers: Sequence[Mapping[str, object]] | None,
        additional_directories: Sequence[str] | None,
        system_prompt: object,
    ) -> dict[str, Any]:
        """Restore a Session without a replay."""
        self._connection()
        self._require("session/resume", "sessionCapabilities.resume")
        servers = self._mcp(mcp_servers)
        self._require_session_args("session/resume", servers, additional_directories, system_prompt)
        request = ResumeSessionRequest(
            session_id=session_id,
            cwd=self._cwd(cwd),
            mcp_servers=servers,
            additional_directories=_listed(additional_directories),
        )
        response = await self._request(
            "session/resume", request, ResumeSessionResponse, system_prompt
        )
        self._state(session_id)
        return _response(response, "modes", "config_options")

    def prompt(self, session_id: str, prompt: object) -> AsyncIterator[dict[str, Any]]:
        """One Prompt Turn: its Session Updates and permission requests, then the response.

        Hands back the turn's own stream, so closing it runs the wind-down in
        the closer's task rather than in a finalizer later.
        """
        conn = self._connection()
        blocks = _blocks(prompt)
        for block in blocks:
            kind = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
            if kind in _GATED_BLOCKS:
                self._require("session/prompt", _GATED_BLOCKS[kind])

        def ask() -> Awaitable[BaseModel]:
            return self._rpc("session/prompt", conn.prompt(session_id=session_id, prompt=blocks))

        return self._turn(session_id, "session/prompt", ask)

    async def cancel(self, session_id: str) -> None:
        """Cancel the Session's Prompt Turn and answer every pending permission request ``cancelled``.

        Never waits for the turn's lock: it is how a running turn is stopped.
        """
        conn = self._connection()
        # Before the notification goes: a request the Agent sends meanwhile is cancelled too.
        self._state(session_id).cancel()
        await self._rpc("session/cancel", conn.cancel(session_id=session_id))

    def answer_permission(self, session_id: str, request: object, option_id: str) -> None:
        """Answer one permission request with one of the options it offered.

        A request already answered, cancelled, or not pending on this
        Session is left alone, so an answer racing a cancel is harmless.
        """
        self._connection()
        state = self._sessions.get(session_id)
        pending = None if state is None else state.pending.get(request)
        if pending is None or pending.answer.done():
            return
        if option_id not in pending.option_ids:
            offered = ", ".join(sorted(pending.option_ids))
            msg = f"permission request {request!r} offers {offered}, not {option_id!r}"
            raise ValueError(msg)
        pending.answer.set_result(option_id)

    async def set_mode(self, session_id: str, mode_id: str) -> None:
        """Switch the Session to one of its ``modes``."""
        conn = self._connection()
        await self._rpc(
            "session/set_mode", conn.set_session_mode(session_id=session_id, mode_id=mode_id)
        )

    async def set_config_option(
        self, session_id: str, config_id: str, value: str | bool
    ) -> list[dict[str, Any]]:
        """Set one config option; the Agent answers with the complete list."""
        conn = self._connection()
        response = await self._rpc(
            "session/set_config_option",
            conn.set_config_option(config_id=config_id, session_id=session_id, value=value),
        )
        return _response(response, "config_options")["config_options"]

    async def close(self, session_id: str) -> None:
        """End the Session on this connection; its history stays with the Agent."""
        conn = self._connection()
        self._require("session/close", "sessionCapabilities.close")
        # Closing cancels the Session's work, so its questions are cancelled too.
        self._state(session_id).cancel()
        await _idempotent(self._rpc("session/close", conn.close_session(session_id=session_id)))

    async def delete(self, session_id: str) -> None:
        """Remove the Session from the Agent's ``list_sessions``."""
        conn = self._connection()
        self._require("session/delete", "sessionCapabilities.delete")
        await _idempotent(self._rpc("session/delete", conn.delete_session(session_id=session_id)))

    def updates(self, session_id: str) -> AsyncIterator[dict[str, Any]]:
        """Every Session Update and permission request for the Session from now on.

        Listens from the call, not from the first pull, so an arm started
        beside a prompt hears the whole turn.
        """
        self._connection()
        if self._lost is not None:
            raise AcpError("session/update", self._lost)
        state = self._state(session_id)
        queue: asyncio.Queue = asyncio.Queue()
        state.subscribers.add(queue)
        return self._listen(state, queue)

    async def _listen(self, state: _Session, queue: asyncio.Queue) -> AsyncIterator[dict[str, Any]]:
        try:
            while True:
                item = await queue.get()
                if isinstance(item, _Closed):
                    if item.error is not None:
                        raise item.error
                    return
                yield item
        finally:
            state.subscribers.discard(queue)

    # --- the two streams ----------------------------------------------------------

    async def _turn(
        self, session_id: str, method: str, start: Callable[[], Awaitable[BaseModel]]
    ) -> AsyncIterator[dict[str, Any]]:
        """Run a request that streams Session Updates while it is open: the items, the response last.

        Holds the Session's lock, so a second prompt or load waits for this
        one. Let go of early, it cancels the turn and waits it out, so the
        Session is idle when the lock passes on.
        """
        if self._lost is not None:
            raise AcpError(method, self._lost)
        state = self._state(session_id)
        async with state.lock:
            items: asyncio.Queue = asyncio.Queue()
            state.turn = items
            state.cancelled = False
            request = asyncio.ensure_future(start())
            request.add_done_callback(lambda _: items.put_nowait(_END))
            request.add_done_callback(_retrieved)
            try:
                while (item := await items.get()) is not _END:
                    if isinstance(item, _Closed):
                        raise item.error or AcpError(method, "the agent connection closed")
                    yield item
                response = request.result()
            finally:
                state.turn = None
                if not request.done():
                    await self._wind_down(session_id, request)
                state.cancelled = False
        if method == "session/prompt":
            yield _response(response, "stop_reason")
        else:
            yield _response(response, "modes", "config_options")

    async def _wind_down(self, session_id: str, request: asyncio.Future) -> None:
        """Cancel a turn its reader let go of, and wait for the Agent to end it.

        The wait is bounded by ``WIND_DOWN``; past it, or with the connection
        gone, the request is dropped, which sends ``$/cancel_request``.
        """
        if self._lost is None and not self._closing:
            with contextlib.suppress(AcpError, RuntimeError):
                await self.cancel(session_id)
            try:
                await asyncio.wait_for(asyncio.shield(request), WIND_DOWN)
            except asyncio.CancelledError:
                request.cancel()
                raise
            except Exception:  # noqa: S110 -- the reader is gone; nobody is left to raise to
                pass
        if not request.done():
            request.cancel()
            with contextlib.suppress(BaseException):
                await request

    async def _request(
        self, method: str, request: BaseModel, response_type: type[M], system_prompt: object
    ) -> M:
        """Send session/new, load or resume, with ``systemPrompt`` when one is given.

        The SDK's typed models predate ``systemPrompt``, so a request that
        carries one is sent raw, and its response validated as the SDK would.
        """
        conn = self._connection()
        if system_prompt is None:
            typed = {
                "session/new": conn.new_session,
                "session/load": conn.load_session,
                "session/resume": conn.resume_session,
            }[method]
            fields = {name: getattr(request, name) for name in type(request).model_fields}
            fields.pop("field_meta", None)
            return await self._rpc(method, typed(**fields))
        params = _wire(request)
        params["systemPrompt"] = _system_prompt(system_prompt)
        raw = await self._rpc(method, conn._conn.send_request(method, params))
        return response_type.model_validate(raw or {})

    def _cwd(self, cwd: str | None) -> str:
        return str(Path(cwd).absolute()) if cwd else self.cwd

    def _mcp(self, servers: Sequence[Mapping[str, object]] | None) -> list[Any]:
        return [dict(server) for server in servers] if servers is not None else self.mcp_servers

    # --- the Agent's calls ----------------------------------------------------------

    def _route(self, session_id: str, update: BaseModel) -> None:
        """One Session Update, to the Session's open turn and every ``updates()`` reader."""
        self._state(session_id).publish(_dump(update))

    async def _permission(
        self, session_id: str, tool_call: BaseModel, options: list[Any]
    ) -> RequestPermissionResponse:
        """Answer by the bind's policy, or ask: yield the request and wait for its answer.

        A request on a Session cancelled since its turn began is answered
        ``cancelled`` whatever the policy: it crossed the cancel on the wire.
        """
        state = self._state(session_id)
        if state.cancelled:
            return _outcome(None)
        if self.permissions != "ask":
            return _outcome(_by_policy(self.permissions, options))
        self._minted += 1
        request_id = self._minted
        pending = _Pending(frozenset(option.option_id for option in options))
        state.pending[request_id] = pending
        # Published before the first await, so it lands in order with the updates around it.
        state.publish(
            {
                "request_permission": request_id,
                "tool_call": _dump(tool_call),
                "options": [_dump(option) for option in options],
            }
        )
        try:
            return _outcome(await pending.answer)
        finally:
            state.pending.pop(request_id, None)


class _Client:
    """The SDK-facing side of the fabric: the methods an Agent may call on its Client.

    Duck-typed rather than subclassing ``acp.Client``, whose stubs would
    answer an unimplemented request with null. Each method the fabric does not
    implement is spelled out and refused with -32601.
    """

    def __init__(self, fabric: AcpFabric) -> None:
        self._fabric = fabric

    async def session_update(self, session_id: str, update: BaseModel, **kwargs: object) -> None:
        # Kept free of awaits: the SDK runs each notification as its own task,
        # and only a handler that never suspends keeps the wire's order.
        self._fabric._route(session_id, update)

    async def request_permission(
        self, session_id: str, tool_call: BaseModel, options: list[Any], **kwargs: object
    ) -> RequestPermissionResponse:
        return await self._fabric._permission(session_id, tool_call, options)

    async def read_text_file(self, **kwargs: object) -> None:
        raise RequestError.method_not_found("fs/read_text_file")

    async def write_text_file(self, **kwargs: object) -> None:
        raise RequestError.method_not_found("fs/write_text_file")

    async def create_terminal(self, **kwargs: object) -> None:
        raise RequestError.method_not_found("terminal/create")

    async def terminal_output(self, **kwargs: object) -> None:
        raise RequestError.method_not_found("terminal/output")

    async def release_terminal(self, **kwargs: object) -> None:
        raise RequestError.method_not_found("terminal/release")

    async def wait_for_terminal_exit(self, **kwargs: object) -> None:
        raise RequestError.method_not_found("terminal/wait_for_exit")

    async def kill_terminal(self, **kwargs: object) -> None:
        raise RequestError.method_not_found("terminal/kill")

    async def create_elicitation(self, **kwargs: object) -> None:
        raise RequestError.method_not_found("elicitation/create")

    async def complete_elicitation(self, **kwargs: object) -> None:
        return None

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        raise RequestError.method_not_found(f"_{method}")

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        return None


# --- shapes -----------------------------------------------------------------------


def _dump(model: BaseModel) -> dict[str, Any]:
    """An SDK model as the wire had it, snake_cased: what the Agent left out stays out."""
    return model.model_dump(mode="json", exclude_unset=True)


def _response(model: BaseModel, *keys: str) -> dict[str, Any]:
    """A response as a dict, its documented ``keys`` always present (None when the Agent left one out)."""
    return {**dict.fromkeys(keys), **_dump(model)}


def _wire(model: BaseModel) -> dict[str, Any]:
    """A request model as JSON-RPC params, camelCase."""
    return model.model_dump(mode="json", by_alias=True, exclude_none=True)


def _blocks(prompt: object) -> list[Any]:
    """A prompt as Content Blocks: a ``str`` is one text block, a list is taken as given."""
    if isinstance(prompt, str):
        return [TextContentBlock(type="text", text=prompt)]
    if isinstance(prompt, (list, tuple)):
        return list(prompt)
    raise TypeError(f"a prompt is a str or a list of Content Block dicts, got {prompt!r}")


def _system_prompt(value: object) -> dict[str, Any]:
    """A ``str`` appends one text block to the Agent's own prompt; a dict is ACP's ``systemPrompt``."""
    if isinstance(value, str):
        return {"mode": "append", "content": [{"type": "text", "text": value}]}
    if isinstance(value, dict):
        return dict(value)
    raise TypeError(f"a system prompt is a str or a systemPrompt dict, got {value!r}")


def _listed(values: Sequence[str] | None) -> list[str] | None:
    return None if values is None else [str(v) for v in values]


def _by_policy(policy: str, options: list[Any]) -> str | None:
    """The option a policy picks: its own kind, else the other kind of the same leaning, else none."""
    for kind in _FALLBACK[policy]:
        for option in options:
            if option.kind == kind:
                return option.option_id
    return None


def _outcome(option_id: str | None) -> RequestPermissionResponse:
    if option_id is None:
        return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
    return RequestPermissionResponse(
        outcome=AllowedOutcome(outcome="selected", option_id=option_id)
    )


def _error(method: str, exc: RequestError) -> AcpError:
    """A JSON-RPC error as an ``AcpError`` that says what to do about it."""
    message = f"{exc} ({exc.code})"
    data = exc.data
    if exc.code == _NOT_FOUND and method.startswith("session/"):
        sid = data.get("sessionId") if isinstance(data, dict) else None
        named = f"session {sid}" if sid else "the session"
        message += (
            f": {named} is unknown or not active on this connection;"
            " start it with new_session, load or resume"
        )
    elif data:
        message += f": {data}"
    return AcpError(method, message, code=exc.code, data=data)


async def _idempotent(call: Awaitable[None]) -> None:
    """Close and delete succeed on a Session that is already gone."""
    try:
        await call
    except AcpError as exc:
        if exc.code != _NOT_FOUND:
            raise


def _retrieved(future: asyncio.Future) -> None:
    """Mark a request's error as seen; a turn let go of early has nobody left to raise it to."""
    if not future.cancelled():
        future.exception()


def _version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("nustd")
    except PackageNotFoundError:
        return "0.0.0+dev"
