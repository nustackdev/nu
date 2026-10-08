"""Functional tests for ``nustd.cc``: prompts, Sessions and their ids, against a fake CLI.

No test here starts ``claude``. The SDK symbols the fabric calls are swapped for
a fake that keeps transcripts in memory and refuses ids the way the CLI does:
``--session-id`` on an id that has a transcript, ``--resume`` on one that has
none. Each reply says how many prompts its conversation has seen, so a test can
tell a continued conversation from a fresh one by the text alone.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

import nu
import nustd.cc
from nustd.cc import fabric


class Agent(nu.Service):
    ask = nustd.cc.PromptRef.method()


class Claude:
    """The CLI as far as these tests need it: transcripts by id, and the two refusals."""

    def __init__(self) -> None:
        self.transcripts: dict[str, list[str]] = {}
        self.clients: list[FakeClient] = []
        self.oneshots: list[object] = []

    def open(self, options: object) -> str:
        """The id a process started with ``options`` runs under, refused as the CLI would."""
        if options.session_id is not None:
            if options.session_id in self.transcripts:
                msg = f"Session ID {options.session_id} is already in use."
                raise RuntimeError(msg)
            return options.session_id
        if options.resume is not None:
            if options.resume not in self.transcripts:
                msg = f"No conversation found with session ID: {options.resume}"
                raise RuntimeError(msg)
            return options.resume
        return str(uuid.uuid4())

    def reply(self, sid: str, prompt: str) -> list[object]:
        said = self.transcripts.setdefault(sid, [])
        said.append(prompt)
        text = f"{len(said)}:{prompt}"
        return [
            AssistantMessage(content=[TextBlock(text=text)], model="fake"),
            ResultMessage(
                subtype="success",
                duration_ms=1,
                duration_api_ms=1,
                is_error=False,
                num_turns=1,
                session_id=sid,
                result=text,
            ),
        ]

    def info(self, sid: str, directory: str | None = None) -> object | None:
        del directory
        return object() if sid in self.transcripts else None


class FakeClient:
    """One process: opened once, answers prompts in order, records its close."""

    def __init__(self, claude: Claude, options: object) -> None:
        self.claude = claude
        self.options = options
        self.sid: str | None = None
        self.pending: list[object] = []
        self.prompts: list[str] = []
        self.disconnected = False
        claude.clients.append(self)

    async def connect(self) -> None:
        self.sid = self.claude.open(self.options)

    async def query(self, prompt: str) -> None:
        self.prompts.append(prompt)
        if prompt == "hang":
            return
        if prompt == "boom":
            msg = "the turn broke"
            raise RuntimeError(msg)
        self.pending = self.claude.reply(self.sid, prompt)

    async def receive_response(self):
        if self.prompts[-1] == "hang":
            await asyncio.sleep(60)
        for msg in self.pending:
            yield msg

    async def disconnect(self) -> None:
        self.disconnected = True


@pytest.fixture
def claude(monkeypatch: pytest.MonkeyPatch) -> Claude:
    world = Claude()

    async def query(*, prompt: str, options: object):
        world.oneshots.append(options)
        sid = world.open(options)
        for msg in world.reply(sid, prompt):
            yield msg

    monkeypatch.setattr(fabric, "query", query)
    monkeypatch.setattr(fabric, "ClaudeSDKClient", lambda options: FakeClient(world, options))
    monkeypatch.setattr(fabric, "get_session_info", world.info)
    return world


def _app(body: nu.Nu, **options: object) -> nu.Nu:
    return nu.With(nustd.cc.bind(Agent, **options), body=body)


async def _arun(body: nu.Nu, **options: object) -> object:
    value, _ = await nu.arun(_app(body, **options))
    return value


def _texts(results: list[dict]) -> list[str]:
    return [one["text"] for one in results]


async def test_a_prompt_outside_a_session_is_one_shot(claude: Claude) -> None:
    got = await _arun(nu.List.of(Agent.ask("a"), Agent.ask("b")))
    assert _texts(got) == ["1:a", "1:b"]
    assert got[0]["session_id"] != got[1]["session_id"]
    assert claude.clients == []
    assert len(claude.oneshots) == 2


async def test_one_session_is_one_process_for_every_prompt(claude: Claude) -> None:
    got = await _arun(nustd.cc.Session(nu.List.of(Agent.ask("a"), Agent.ask("b"), Agent.ask("c"))))
    assert _texts(got) == ["1:a", "2:b", "3:c"]
    (client,) = claude.clients
    assert client.prompts == ["a", "b", "c"]
    assert claude.oneshots == []


async def test_a_fresh_session_hands_its_id_back_in_every_result(claude: Claude) -> None:
    got = await _arun(nustd.cc.Session(nu.List.of(Agent.ask("a"), Agent.ask("b"))))
    (client,) = claude.clients
    assert got[0]["session_id"] == got[1]["session_id"] == client.sid
    assert client.options.session_id is None
    assert client.options.resume is None


async def test_a_given_id_is_the_id_of_the_first_prompt(claude: Claude) -> None:
    sid = str(uuid.uuid4())
    got = await _arun(nustd.cc.Session(Agent.ask("a"), sid=sid))
    assert got["session_id"] == sid
    (client,) = claude.clients
    assert client.options.session_id == sid
    assert client.options.resume is None


async def test_a_minted_id_can_be_held_before_anything_is_said(claude: Claude) -> None:
    body = nu.let(
        nustd.cc.NewSession(),
        lambda sid: nu.List.of(sid, nustd.cc.Session(Agent.ask("a"), sid=sid)),
    )
    sid, got = await _arun(body)
    assert str(uuid.UUID(sid)) == sid
    assert got["session_id"] == sid


async def test_a_second_session_on_the_same_id_continues_it(claude: Claude) -> None:
    sid = str(uuid.uuid4())
    first = await _arun(nustd.cc.Session(Agent.ask("a"), sid=sid))
    second = await _arun(nustd.cc.Session(Agent.ask("b"), sid=sid))
    assert (first["text"], second["text"]) == ("1:a", "2:b")
    opened, resumed = claude.clients
    assert opened.options.session_id == sid
    assert resumed.options.resume == sid
    assert resumed.options.session_id is None


async def test_nested_sessions_shadow(claude: Claude) -> None:
    inner = nustd.cc.Session(Agent.ask("x"))
    got = await _arun(nustd.cc.Session(nu.List.of(Agent.ask("a"), inner, Agent.ask("b"))))
    assert _texts(got) == ["1:a", "1:x", "2:b"]
    assert len(claude.clients) == 2


async def test_the_process_stops_when_the_session_ends(claude: Claude) -> None:
    await _arun(nustd.cc.Session(Agent.ask("a")))
    (client,) = claude.clients
    assert client.disconnected


async def test_the_process_stops_when_the_body_fails(claude: Claude) -> None:
    body = nustd.cc.Session(nu.List.of(Agent.ask("a"), nu.Div(1, 0)))
    with pytest.raises(ZeroDivisionError):
        await _arun(body)
    (client,) = claude.clients
    assert client.disconnected


async def test_the_process_stops_when_the_session_is_cancelled(claude: Claude) -> None:
    body = nu.Timeout(0.05, nustd.cc.Session(nu.List.of(Agent.ask("a"), Agent.ask("hang"))))
    with pytest.raises(TimeoutError):
        await _arun(body)
    (client,) = claude.clients
    assert client.disconnected


async def test_a_failed_turn_reopens_on_the_same_id(claude: Claude) -> None:
    """A turn that broke may have left half a reply on the stream, so the
    process goes, and the next prompt opens a new one on the conversation."""
    caught = nu.TryCatch(Agent.ask("boom"), catch=nu.Str("caught"))
    body = nustd.cc.Session(nu.List.of(Agent.ask("a"), caught, Agent.ask("b")))
    got = await _arun(body)
    assert (got[0]["text"], got[2]["text"]) == ("1:a", "2:b")
    broken, reopened = claude.clients
    assert broken.disconnected
    assert reopened.options.resume == got[0]["session_id"]


async def test_one_process_takes_one_set_of_options(claude: Claude) -> None:
    body = nustd.cc.Session(nu.List.of(Agent.ask("a"), Agent.ask("b", model="other")))
    with pytest.raises(ValueError, match="one claude process"):
        await _arun(body)
    (client,) = claude.clients
    assert client.disconnected


async def test_an_id_that_is_not_a_uuid_is_refused(claude: Claude) -> None:
    with pytest.raises(ValueError, match="badly formed"):
        await _arun(nustd.cc.Session(Agent.ask("a"), sid="not-an-id"))
    assert claude.clients == []


def test_the_sync_path_is_a_process_per_prompt_on_the_sessions_id(claude: Claude) -> None:
    sid = str(uuid.uuid4())
    got, _ = nu.run(_app(nustd.cc.Session(nu.List.of(Agent.ask("a"), Agent.ask("b")), sid=sid)))
    assert _texts(got) == ["1:a", "2:b"]
    assert [one["session_id"] for one in got] == [sid, sid]
    first, second = claude.oneshots
    assert (first.session_id, first.resume) == (sid, None)
    assert (second.session_id, second.resume) == (None, sid)
    assert claude.clients == []


def test_the_sync_path_carries_a_fresh_sessions_id_forward(claude: Claude) -> None:
    got, _ = nu.run(_app(nustd.cc.Session(nu.List.of(Agent.ask("a"), Agent.ask("b")))))
    assert _texts(got) == ["1:a", "2:b"]
    assert got[0]["session_id"] == got[1]["session_id"]


def test_the_sync_path_outside_a_session_is_one_shot(claude: Claude) -> None:
    got, _ = nu.run(_app(Agent.ask("a")))
    assert got["text"] == "1:a"
    assert len(claude.oneshots) == 1
