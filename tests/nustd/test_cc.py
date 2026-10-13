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
from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

import nu
import nustd.cc
from nustd.cc import fabric


class Agent(nu.Service):
    ask = nustd.cc.PromptRef.method()
    say = nustd.cc.StreamRef.method()


class Claude:
    """The CLI as far as these tests need it: transcripts by id, and the two refusals."""

    def __init__(self) -> None:
        self.transcripts: dict[str, list[str]] = {}
        self.clients: list[FakeClient] = []
        self.oneshots: list[object] = []
        #: Set by a test to let a reply past its first message (prompts starting with ``gate``).
        self.gate = asyncio.Event()
        #: Whether a stream's messages were drained to the end, by prompt.
        self.drained: dict[str, bool] = {}

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
        work: list[object] = []
        if prompt.startswith("tool"):
            work = [
                SystemMessage(
                    subtype="init", data={"session_id": sid, "model": "fake", "cwd": "/w"}
                ),
                AssistantMessage(
                    content=[
                        TextBlock(text="looking"),
                        ToolUseBlock(id="t1", name="Bash", input={"command": "ls"}),
                    ],
                    model="fake",
                ),
                UserMessage(content=[ToolResultBlock(tool_use_id="t1", content="x" * 5000)]),
            ]
        return [
            *work,
            AssistantMessage(content=[TextBlock(text=text)], model="fake"),
            ResultMessage(
                subtype="success",
                duration_ms=1,
                duration_api_ms=1,
                is_error=False,
                num_turns=1,
                session_id=sid,
                result=text,
                total_cost_usd=0.01,
                usage={"input_tokens": 3, "output_tokens": 4},
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
        async for msg in _paced(self.claude, self.prompts[-1], self.pending):
            yield msg

    async def disconnect(self) -> None:
        self.disconnected = True


async def _paced(claude: Claude, prompt: str, messages: list[object]):
    """``messages`` in order; a ``gate`` prompt waits for the test after the first, ``slow`` forever."""
    claude.drained[prompt] = False
    for i, msg in enumerate(messages):
        if i == 1 and prompt.startswith("gate"):
            await claude.gate.wait()
        if i == 1 and prompt.startswith("slow"):
            await asyncio.sleep(60)
        yield msg
    claude.drained[prompt] = True


@pytest.fixture
def claude(monkeypatch: pytest.MonkeyPatch) -> Claude:
    world = Claude()

    async def query(*, prompt: str, options: object):
        world.oneshots.append(options)
        sid = world.open(options)
        async for msg in _paced(world, prompt, world.reply(sid, prompt)):
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


# --- streaming -------------------------------------------------------------------------------


def _types(events: list[dict]) -> list[str]:
    return [one["type"] for one in events]


async def test_a_stream_hands_over_the_turn_then_its_result(claude: Claude) -> None:
    got = await _arun(nu.Collect(Agent.say("a")))
    assert _types(got) == ["text", "result"]
    text, result = got
    assert text["text"] == "1:a"
    assert result["text"] == "1:a"
    assert result["total_cost_usd"] == 0.01
    assert result["usage"] == {"input_tokens": 3, "output_tokens": 4}
    assert result["is_error"] is False
    assert len(claude.oneshots) == 1


async def test_a_stream_says_its_tool_calls_and_what_they_gave_back(claude: Claude) -> None:
    got = await _arun(nu.Collect(Agent.say("tool")))
    assert _types(got) == ["init", "text", "tool_use", "tool_result", "text", "result"]
    init, _, use, back, _, _ = got
    assert init["session_id"] == got[-1]["session_id"]
    assert (use["id"], use["name"], use["input"]) == ("t1", "Bash", {"command": "ls"})
    assert back["id"] == "t1"
    assert back["is_error"] is False
    assert back["content"].startswith("x" * fabric.TRIM)
    assert back["content"].endswith("3,000 more characters")


async def test_events_arrive_while_the_turn_is_still_going(
    claude: Claude, capsys: pytest.CaptureFixture[str]
) -> None:
    """The first event is out before the fake lets the rest of the reply through."""
    run = asyncio.create_task(
        _arun(nu.ForEachDo(Agent.say("gate"), lambda ev: nu.print(ev["type"])))
    )
    seen = ""
    for _ in range(100):
        seen += capsys.readouterr().out
        if seen:
            break
        await asyncio.sleep(0.01)
    assert seen.split() == ["text"]
    assert not run.done()
    claude.gate.set()
    await asyncio.wait_for(run, 5)
    assert (seen + capsys.readouterr().out).split() == ["text", "result"]


async def test_a_stream_in_a_session_is_a_turn_of_its_conversation(claude: Claude) -> None:
    body = nustd.cc.Session(nu.List.of(Agent.ask("a"), nu.Collect(Agent.say("b")), Agent.ask("c")))
    first, streamed, last = await _arun(body)
    assert (first["text"], streamed[-1]["text"], last["text"]) == ("1:a", "2:b", "3:c")
    (client,) = claude.clients
    assert client.prompts == ["a", "b", "c"]


async def test_a_stream_read_to_its_result_keeps_the_process(claude: Claude) -> None:
    body = nustd.cc.Session(nu.List.of(nu.Collect(Agent.say("a")), nu.Collect(Agent.say("b"))))
    a, b = await _arun(body)
    assert (a[-1]["text"], b[-1]["text"]) == ("1:a", "2:b")
    assert len(claude.clients) == 1


async def test_letting_go_of_a_stream_early_closes_the_process(claude: Claude) -> None:
    """The rest of the reply is left on the stream, so the next prompt opens a new process."""
    body = nustd.cc.Session(nu.List.of(nu.First(Agent.say("tool")), Agent.ask("b")))
    first, after = await _arun(body)
    assert first["type"] == "init"
    assert claude.drained["tool"] is False
    broken, reopened = claude.clients
    assert broken.disconnected
    assert reopened.options.resume == after["session_id"]
    assert after["text"] == "2:b"


async def test_a_cancelled_stream_closes_the_process(claude: Claude) -> None:
    body = nu.Timeout(0.05, nustd.cc.Session(nu.Collect(Agent.say("slow"))))
    with pytest.raises(TimeoutError):
        await _arun(body)
    (client,) = claude.clients
    assert client.disconnected


def test_the_sync_path_streams_too(claude: Claude) -> None:
    got, _ = nu.run(_app(nu.Collect(Agent.say("tool"))))
    assert _types(got) == ["init", "text", "tool_use", "tool_result", "text", "result"]
    assert len(claude.oneshots) == 1


def test_the_sync_path_streams_a_sessions_turns_on_its_id(claude: Claude) -> None:
    sid = str(uuid.uuid4())
    body = nustd.cc.Session(nu.List.of(nu.Collect(Agent.say("a")), Agent.ask("b")), sid=sid)
    (streamed, asked), _ = nu.run(_app(body))
    assert (streamed[-1]["session_id"], asked["session_id"]) == (sid, sid)
    assert asked["text"] == "2:b"


def test_the_sync_path_stops_the_stream_it_lets_go_of(claude: Claude) -> None:
    got, _ = nu.run(_app(nu.First(Agent.say("slow"))))
    assert got["type"] == "text"
    assert claude.drained["slow"] is False


def test_partial_messages_become_deltas() -> None:
    piece = {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "he"}}
    other = {"type": "message_start"}
    assert fabric.events_of(StreamEvent(uuid="u", session_id="s", event=piece)) == [
        {"type": "delta", "text": "he"}
    ]
    assert fabric.events_of(StreamEvent(uuid="u", session_id="s", event=other)) == []


def test_a_tool_result_in_parts_reads_as_text() -> None:
    parts = [{"type": "text", "text": "one"}, {"type": "image", "source": {}}]
    msg = UserMessage(content=[ToolResultBlock(tool_use_id="t", content=parts, is_error=True)])
    assert fabric.events_of(msg) == [
        {"type": "tool_result", "id": "t", "content": "one\n[image]", "is_error": True}
    ]
