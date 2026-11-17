"""The Agent side of ``nustd.acp``: setup, binding, and the methods on the AgentRef.

Every test spawns the scripted Agent in ``_support/acp_agent.py`` as a real
subprocess and talks ACP v1 to it over stdio. No real coding agent runs.
"""

from __future__ import annotations

import sys

import pytest
from _support.acp_fixtures import FAKE, Agent, Log, bound, run, stats_of

import nu
import nustd.acp
from nustd.acp import AcpError, AcpFabric


pytestmark = pytest.mark.timeout(20, method="thread")

BARE = {"FAKE_ACP_BARE": "1"}


def new_sid() -> nu.Nu:
    return nu.Dict(Agent.new_session())["session_id"]


async def test_initialization_is_what_setup_got():
    init, _ = await run(Agent.initialization())
    assert init["protocol_version"] == 1
    assert init["agent_info"] == {"name": "fake", "version": "1.0"}
    assert init["agent_capabilities"]["load_session"] is True


async def test_an_agent_on_another_version_is_refused():
    with pytest.raises(AcpError, match=r"ACP version 2; nustd\.acp speaks version 1 only"):
        await run(Agent.initialization(), env={"FAKE_ACP_VERSION": "2"})


async def test_a_chatty_agent_never_stalls_on_its_stderr():
    init, _ = await run(Agent.initialization(), env={"FAKE_ACP_STDERR_KB": "1024"})
    assert init["protocol_version"] == 1


async def test_a_refused_agent_is_stopped():
    fabric = AcpFabric(command=FAKE, env={"FAKE_ACP_VERSION": "7"})
    with pytest.raises(AcpError):
        await fabric.asetup(None)
    assert fabric._watchers == []
    with pytest.raises(RuntimeError, match="not running"):
        fabric.initialization()


async def test_an_agent_that_exits_at_once_fails_setup():
    # Whichever the fabric notices first, the closed pipe or the exit, it names.
    closed = r"initialize: (the connection to the agent is closed|the agent exited with code 0)"
    with pytest.raises(AcpError, match=closed):
        await nu.arun(
            nu.With(
                nustd.acp.bind(Agent, command=[sys.executable, "-c", "pass"]),
                body=Agent.initialization(),
            )
        )


async def test_a_missing_command_fails_setup():
    with pytest.raises(AcpError, match="cannot start"):
        await nu.arun(
            nu.With(
                nustd.acp.bind(Agent, command=["/no/such/agent-binary"]),
                body=Agent.initialization(),
            )
        )


async def test_new_session_yields_the_response():
    session, _ = await run(Agent.new_session())
    assert session["session_id"] == "s1"
    assert session["modes"]["current_mode_id"] == "default"
    assert [o["id"] for o in session["config_options"]] == ["model", "fast"]


async def test_new_session_takes_the_bind_defaults_and_call_overrides(tmp_path):
    server = {"name": "tools", "command": "/bin/true", "args": [], "env": []}
    other = tmp_path / "other"
    body = nu.Sequential(
        nu.let(new_sid(), lambda sid: nu.ForEachDo(Agent[sid].prompt("stats"), Log.a.append)),
        Agent.new_session(cwd=str(other), mcp_servers=[]),
        nu.let(new_sid(), lambda sid: nu.ForEachDo(Agent[sid].prompt("stats"), Log.b.append)),
    )
    _, log = await run(body, cwd=str(tmp_path), mcp_servers=[server])
    stats = stats_of(log["b"])
    assert stats["cwd"] == {"s1": str(tmp_path), "s2": str(other), "s3": str(tmp_path)}
    assert stats["mcp"] == {"s1": ["tools"], "s2": [], "s3": ["tools"]}


async def test_new_session_sends_a_system_prompt_raw(tmp_path):
    override = {"mode": "append", "content": [{"type": "text", "text": "be terse"}]}
    body = nu.Sequential(
        Agent.new_session(system_prompt="answer in one word", additional_directories=["/extra"]),
        Agent.new_session(system_prompt=override),
        Agent.new_session(),
        nu.let(new_sid(), lambda sid: nu.ForEachDo(Agent[sid].prompt("stats"), Log.a.append)),
    )
    _, log = await run(body, cwd=str(tmp_path))
    raw = stats_of(log["a"])["raw_new"]
    assert raw[0] == {
        "cwd": str(tmp_path),
        "mcpServers": [],
        "additionalDirectories": ["/extra"],
        "systemPrompt": {
            "mode": "append",
            "content": [{"type": "text", "text": "answer in one word"}],
        },
    }
    assert raw[1]["systemPrompt"] == override
    assert "systemPrompt" not in raw[2]


HTTP = {"type": "http", "name": "web", "url": "http://localhost:1", "headers": []}
SSE = {"type": "sse", "name": "events", "url": "http://localhost:1", "headers": []}


def _prompt_with(block):
    return nu.let(new_sid(), lambda sid: nu.Collect(Agent[sid].prompt([block])))


@pytest.mark.parametrize(
    ("body", "capability"),
    [
        (lambda: nu.Collect(Agent["old"].load()), "loadSession"),
        (lambda: Agent["old"].resume(), "sessionCapabilities.resume"),
        (lambda: nu.let(new_sid(), lambda sid: Agent[sid].close()), "sessionCapabilities.close"),
        (lambda: Agent["k1"].delete(), "sessionCapabilities.delete"),
        (lambda: nu.Collect(Agent.list_sessions()), "sessionCapabilities.list"),
        (lambda: Agent.logout(), "auth.logout"),
        (
            lambda: Agent.new_session(additional_directories=["/x"]),
            "sessionCapabilities.additionalDirectories",
        ),
        (lambda: Agent.new_session(system_prompt="hi"), "sessionCapabilities.systemPrompt"),
        (lambda: Agent.new_session(mcp_servers=[HTTP]), "mcpCapabilities.http"),
        (
            lambda: _prompt_with({"type": "image", "data": "AA==", "mime_type": "image/png"}),
            "promptCapabilities.image",
        ),
        (
            lambda: _prompt_with({"type": "audio", "data": "AA==", "mime_type": "audio/wav"}),
            "promptCapabilities.audio",
        ),
        (
            lambda: _prompt_with(
                {"type": "resource", "resource": {"uri": "file:///a", "text": "a"}}
            ),
            "promptCapabilities.embeddedContext",
        ),
    ],
)
async def test_a_bare_agent_is_never_sent_what_it_did_not_advertise(body, capability):
    with pytest.raises(AcpError, match=f"does not advertise agentCapabilities.{capability}$") as c:
        await run(body(), env=BARE)
    assert c.value.code == -32601


@pytest.mark.parametrize(
    ("body", "capability"),
    [
        (
            lambda: Agent.new_session(
                system_prompt={"mode": "override", "content": [{"type": "text", "text": "x"}]}
            ),
            "sessionCapabilities.systemPrompt.mode.override",
        ),
        (lambda: Agent.new_session(mcp_servers=[SSE]), "mcpCapabilities.sse"),
        (lambda: Agent.new_session(mcp_servers=[]), None),
        (
            lambda: _prompt_with({"type": "audio", "data": "AA==", "mime_type": "audio/wav"}),
            "promptCapabilities.audio",
        ),
    ],
)
async def test_capabilities_gate_down_to_the_field(body, capability):
    if capability is None:
        await run(body())
        return
    with pytest.raises(AcpError, match=f"agentCapabilities.{capability}$"):
        await run(body())


async def test_what_is_always_allowed_passes_a_bare_agent():
    link = {"type": "resource_link", "uri": "file:///a", "name": "a"}
    body = nu.let(
        new_sid(), lambda sid: nu.Last(Agent[sid].prompt([{"type": "text", "text": "hello"}, link]))
    )
    stop, _ = await run(body, env=BARE)
    assert stop == {"stop_reason": "end_turn"}


async def test_a_refused_request_never_reaches_the_agent():
    fabric = AcpFabric(command=FAKE, env=BARE)
    await fabric.asetup(None)
    try:
        with pytest.raises(AcpError, match="systemPrompt"):
            await fabric.new_session(None, None, None, "hi")
        sid = (await fabric.new_session(None, None, None, None))["session_id"]
        items = [item async for item in fabric.prompt(sid, "stats")]
        assert len(stats_of(items)["raw_new"]) == 1
    finally:
        await fabric.acleanup()


async def test_list_sessions_follows_every_page():
    sessions, _ = await run(nu.Collect(Agent.list_sessions()))
    assert [s["session_id"] for s in sessions] == ["k0", "k1", "k2", "k3", "k4"]
    assert sessions[0] == {"session_id": "k0", "cwd": "/w/0", "title": "t-k0", "updated_at": None}


async def test_list_sessions_filters_by_cwd():
    sessions, _ = await run(nu.Collect(Agent.list_sessions(cwd="/w/3")))
    assert [s["session_id"] for s in sessions] == ["k3"]


async def test_authenticate_and_logout_reach_the_agent():
    body = nu.Sequential(
        Agent.authenticate("key"),
        Agent.logout(),
        nu.let(new_sid(), lambda sid: nu.ForEachDo(Agent[sid].prompt("stats"), Log.a.append)),
    )
    _, log = await run(body)
    stats = stats_of(log["a"])
    assert stats["auth"] == ["key"]
    assert stats["logout"] == 1


async def test_the_client_refuses_what_it_does_not_implement():
    body = nu.let(new_sid(), lambda sid: nu.ForEachDo(Agent[sid].prompt("client"), Log.a.append))
    _, log = await run(body)
    codes = stats_of(log["a"])
    assert codes == {"fs/read_text_file": -32601, "terminal/create": -32601, "_x/ping": -32601}


async def test_exists_reads_the_named_binding():
    inside, _ = await run(Agent.exists())
    outside, _ = await nu.arun(Agent.exists())
    other, _ = await run(nustd.acp.AgentRef("other").exists())
    assert (inside, outside, other) == (True, False, False)


async def test_an_unbound_agent_says_how_to_bind_one():
    with pytest.raises(RuntimeError, match=r"no ACP agent is bound for fake: wrap the tree"):
        await nu.arun(Agent.new_session())


def test_the_sync_runner_is_refused():
    with pytest.raises(RuntimeError, match=r"async-only atom \(AcpNewSession\)"):
        nu.run(bound(Agent.new_session()))


def test_the_fabric_refuses_the_sync_runner_on_its_own():
    with pytest.raises(RuntimeError, match="AcpFabric requires the async runner"):
        nu.run(nu.With(nustd.acp.bind(Agent, command=FAKE), body=Agent.exists()))


@pytest.mark.parametrize(
    ("preset", "command"),
    [
        (nustd.acp.claude, ["npx", "-y", "@agentclientprotocol/claude-agent-acp"]),
        (nustd.acp.codex, ["npx", "-y", "@agentclientprotocol/codex-acp"]),
        (nustd.acp.gemini, ["gemini", "--acp"]),
        (nustd.acp.opencode, ["opencode", "acp"]),
    ],
)
def test_presets_are_the_command_and_the_name(preset, command):
    spec = preset(Agent, cwd="/srv", permissions="allow_once")
    payload = spec._payload
    assert payload["cls"] is AcpFabric
    assert payload["tags"] == ("fake",)
    assert payload["kwargs"]["command"] == command
    assert payload["kwargs"]["cwd"] == "/srv"
    assert payload["kwargs"]["permissions"] == "allow_once"


def test_bind_checks_its_arguments():
    with pytest.raises(ValueError, match="permissions is one of"):
        nustd.acp.bind(Agent, command=FAKE, permissions="yes")
    with pytest.raises(TypeError, match="argv"):
        nustd.acp.bind(Agent, command="npx claude")
    with pytest.raises(TypeError, match="AgentRef or its name"):
        nustd.acp.bind("", command=FAKE)
