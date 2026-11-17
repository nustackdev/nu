"""The Session side of ``nustd.acp``: Prompt Turns, cancel, load and resume, and ``updates()``.

Every test runs against the scripted Agent in ``_support/acp_agent.py``, a
real subprocess spoken to over stdio. The prompt's text picks the turn.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import time

import pytest
from _support.acp_fixtures import FAKE, Agent, Log, has, run, stats_of, texts

import nu
from nustd.acp import AcpError, AcpFabric
from nustd.acp import fabric as fabric_module


pytestmark = pytest.mark.timeout(20, method="thread")


def with_session(body):
    """``body(sid)`` on a fresh Session."""
    return nu.let(nu.Dict(Agent.new_session())["session_id"], body)


def log_all(stream, into=Log.a):
    return nu.ForEachDo(stream, into.append)


def is_chunk(item, text):
    return nu.And(
        has(item, "session_update"),
        nu.Dict(item)["session_update"] == "agent_message_chunk",
        nu.Dict(nu.Dict(item)["content"])["text"] == text,
    )


# --- Prompt Turns -------------------------------------------------------------------


async def test_a_prompt_streams_its_updates_then_the_stop_reason():
    _, log = await run(with_session(lambda sid: log_all(Agent[sid].prompt("hello"))))
    items = log["a"]
    assert texts(items) == ["hel", "lo"]
    assert items[-1] == {"stop_reason": "end_turn"}
    assert items[0] == {
        "session_update": "agent_message_chunk",
        "content": {"type": "text", "text": "hel"},
    }


async def test_a_prompt_takes_content_blocks():
    blocks = [{"type": "text", "text": "hello"}]
    _, log = await run(with_session(lambda sid: log_all(Agent[sid].prompt(blocks))))
    assert texts(log["a"]) == ["hel", "lo"]


async def test_nu_last_is_the_stop_reason():
    stop, _ = await run(with_session(lambda sid: nu.Last(Agent[sid].prompt("hello"))))
    assert stop == {"stop_reason": "end_turn"}


async def test_one_prompt_turn_at_a_time_per_session():
    body = with_session(
        lambda sid: nu.ParallelAsync(
            log_all(Agent[sid].prompt("slow"), Log.a),
            log_all(Agent[sid].prompt("probe"), Log.b),
        )
    )
    _, log = await run(body)
    # The fake counts the prompts running on the Session as the probe begins.
    assert texts(log["b"]) == ["1"]
    assert log["a"][-1] == {"stop_reason": "end_turn"}


async def test_two_sessions_run_their_turns_independently():
    # s1's turn holds until cancelled; s2 runs a whole turn inside it, then cancels s1.
    _, log = await run(with_session(lambda s1: with_session(lambda s2: _two_sessions(s1, s2))))
    assert texts(log["b"]) == ["hel", "lo"]
    assert log["b"][-1] == {"stop_reason": "end_turn"}
    assert texts(log["a"]) == ["waiting", "stopped"]
    assert log["a"][-1] == {"stop_reason": "cancelled"}


def _two_sessions(s1, s2):
    return nu.ForEachDo(
        Agent[s1].prompt("wait"),
        lambda item: nu.Sequential(
            Log.a.append(item),
            nu.IfDo(
                is_chunk(item, "waiting"),
                nu.Sequential(log_all(Agent[s2].prompt("hello"), Log.b), Agent[s1].cancel()),
            ),
        ),
    )


async def test_cancel_ends_the_turn_with_cancelled():
    body = with_session(
        lambda sid: nu.ForEachDo(
            Agent[sid].prompt("wait"),
            lambda item: nu.Sequential(
                Log.a.append(item),
                nu.IfDo(is_chunk(item, "waiting"), Agent[sid].cancel()),
            ),
        )
    )
    _, log = await run(body)
    assert texts(log["a"]) == ["waiting", "stopped"]
    assert log["a"][-1] == {"stop_reason": "cancelled"}


async def test_letting_go_of_a_prompt_early_cancels_the_turn():
    # The stats prompt can only run once the abandoned turn has ended: one turn at a time.
    body = with_session(
        lambda sid: nu.Sequential(
            Log.a.append(nu.First(Agent[sid].prompt("wait"))),
            log_all(Agent[sid].prompt("stats"), Log.b),
        )
    )
    _, log = await run(body)
    assert texts(log["a"]) == ["waiting"]
    assert stats_of(log["b"])["cancels"] == {"s1": 1}


async def test_a_session_not_active_raises():
    with pytest.raises(AcpError, match="session nope is unknown or not active") as caught:
        await run(nu.Collect(Agent["nope"].prompt("hello")))
    assert caught.value.code == -32002
    assert caught.value.method == "session/prompt"


async def test_an_agent_that_dies_fails_its_streams():
    body = with_session(
        lambda sid: nu.Race(
            log_all(Agent[sid].updates(), Log.b),
            log_all(Agent[sid].prompt("die")),
        )
    )
    with pytest.raises(AcpError, match=r"exited with code 3|connection to the agent is closed"):
        await run(body)


async def test_updates_raise_when_the_agent_dies():
    fabric = AcpFabric(command=FAKE)
    await fabric.asetup(None)
    try:
        sid = (await fabric.new_session(None, None, None, None))["session_id"]
        updates = fabric.updates(sid)
        first = asyncio.ensure_future(updates.__anext__())
        with pytest.raises(AcpError):
            async for _ in fabric.prompt(sid, "die"):
                pass
        assert (await first)["content"]["text"] == "dying"
        with pytest.raises(AcpError, match="the agent exited with code 3"):
            await asyncio.wait_for(updates.__anext__(), 5)
    finally:
        await fabric.acleanup()


async def test_an_agent_whose_child_holds_stdout_still_fails_its_streams():
    # The pipe never reaches its end; the exit alone must end the turn.
    fabric = AcpFabric(command=FAKE)
    await fabric.asetup(None)
    orphan = None
    try:
        sid = (await fabric.new_session(None, None, None, None))["session_id"]
        items = []
        with pytest.raises(AcpError, match="the agent exited with code 3"):
            async for item in fabric.prompt(sid, "orphan"):
                items.append(item)
        orphan = int(texts(items)[0].split(":")[1])
        os.kill(orphan, 0)  # still alive, still holding the pipe
        with pytest.raises(AcpError, match="exited with code 3"):
            await fabric.new_session(None, None, None, None)
    finally:
        # The orphan goes first, so the pipe it held closes while this loop still runs.
        if orphan is not None:
            with contextlib.suppress(ProcessLookupError):
                os.kill(orphan, signal.SIGKILL)
        await asyncio.wait_for(fabric.acleanup(), 10)


# --- letting go early ------------------------------------------------------------------


async def _fabric(**kwargs):
    fabric = AcpFabric(command=FAKE, **kwargs)
    await fabric.asetup(None)
    sid = (await fabric.new_session(None, None, None, None))["session_id"]
    return fabric, sid


async def test_closing_a_prompt_early_waits_the_turn_out_in_the_closer():
    fabric, sid = await _fabric()
    try:
        stream = fabric.prompt(sid, "wait")
        assert texts([await stream.__anext__()]) == ["waiting"]
        await asyncio.wait_for(stream.aclose(), 5)
        # Wound down before aclose returned: the lock is free, the Agent saw one cancel.
        assert not fabric._sessions[sid].lock.locked()
        stats = stats_of([item async for item in fabric.prompt(sid, "stats")])
        assert stats["cancels"] == {sid: 1}
    finally:
        await fabric.acleanup()


@pytest.mark.parametrize("permissions", ["ask", "allow_once"])
async def test_closing_early_answers_a_request_that_crosses_the_cancel(permissions):
    fabric, sid = await _fabric(permissions=permissions)
    try:
        stream = fabric.prompt(sid, "late")
        assert texts([await stream.__anext__()]) == ["go"]
        await asyncio.wait_for(stream.aclose(), 5)
        assert not fabric._sessions[sid].lock.locked()
        assert fabric._sessions[sid].pending == {}
        after = [item async for item in fabric.prompt(sid, "hello")]
        assert after[-1] == {"stop_reason": "end_turn"}
    finally:
        await fabric.acleanup()


async def test_a_turn_that_ignores_its_cancel_is_dropped_after_the_wind_down(monkeypatch):
    monkeypatch.setattr(fabric_module, "WIND_DOWN", 0.3)
    fabric, sid = await _fabric()
    try:
        stream = fabric.prompt(sid, "stubborn")
        assert texts([await stream.__anext__()]) == ["ignoring"]
        started = time.monotonic()
        await asyncio.wait_for(stream.aclose(), 5)
        assert time.monotonic() - started < 3
        assert not fabric._sessions[sid].lock.locked()
        after = [item async for item in fabric.prompt(sid, "hello")]
        assert texts(after) == ["hel", "lo"]
    finally:
        await fabric.acleanup()


# --- load, resume, close, delete ----------------------------------------------------------


async def test_load_replays_then_yields_the_response():
    body = nu.Sequential(log_all(Agent["old"].load()), log_all(Agent["old"].prompt("hello"), Log.b))
    _, log = await run(body)
    replay, response = log["a"][:-1], log["a"][-1]
    assert [u["session_update"] for u in replay] == ["user_message_chunk", "agent_message_chunk"]
    assert [u["content"]["text"] for u in replay] == ["what is 2+2", "4"]
    assert response["modes"]["current_mode_id"] == "default"
    assert response["config_options"] is None
    assert texts(log["b"]) == ["hel", "lo"]


async def test_load_of_an_unknown_session_raises():
    with pytest.raises(AcpError, match="session/load"):
        await run(nu.Collect(Agent["gone"].load()))


async def test_resume_makes_a_session_active_without_a_replay():
    body = nu.Sequential(
        log_all(Agent["old"].updates(), Log.b) & Agent["old"].resume(),
        log_all(Agent["old"].prompt("hello")),
    )
    _, log = await run(body)
    assert log["b"] == []
    assert texts(log["a"]) == ["hel", "lo"]


async def test_resume_yields_the_response():
    response, _ = await run(Agent["old"].resume())
    assert response["modes"] is None
    assert response["config_options"][0]["id"] == "model"


async def test_a_closed_session_is_inactive_and_closing_twice_is_fine():
    body = with_session(
        lambda sid: nu.Sequential(
            Agent[sid].close(),
            Agent[sid].close(),
            log_all(Agent[sid].prompt("hello")),
        )
    )
    with pytest.raises(AcpError, match="not active"):
        await run(body)


async def test_delete_drops_the_session_from_the_list_and_twice_is_fine():
    body = nu.Sequential(
        Agent["k1"].delete(),
        Agent["k1"].delete(),
        log_all(Agent.list_sessions()),
    )
    _, log = await run(body)
    assert [s["session_id"] for s in log["a"]] == ["k0", "k2", "k3", "k4"]


Old = Agent["old"]


async def test_one_ref_serves_every_term_of_a_tree_through_a_rewrite():
    """One module-level Session ref in many terms, across parallel arms, survives a rewrite pass."""
    body = nu.Sequential(
        Old.resume(),
        nu.ParallelAsync(
            log_all(Old.prompt("hello"), Log.a),
            log_all(Agent.list_sessions(), Log.b),
            Log.c.append(Agent.initialization()),
        ),
        Old.set_mode("plan"),
        log_all(Old.prompt("stats"), Log.c),
    )
    assert sum(node is Old for node in nu.tree.preorder(body)) == 4
    assert sum(node is Agent for node in nu.tree.preorder(body)) == 6
    rebuilt = nu.tree.map_nodes(body, lambda node: node)
    assert rebuilt is not body
    _, log = await run(rebuilt)
    assert texts(log["a"]) == ["hel", "lo"]
    assert log["a"][-1] == {"stop_reason": "end_turn"}
    assert [s["session_id"] for s in log["b"]] == ["k0", "k1", "k2", "k3", "k4"]
    assert log["c"][0]["agent_info"] == {"name": "fake", "version": "1.0"}
    assert stats_of(log["c"])["modes"] == {"old": "plan"}


# --- modes and config ----------------------------------------------------------------


async def test_set_config_option_yields_every_option():
    body = with_session(
        lambda sid: nu.let(
            Agent[sid].set_config_option("fast", True),
            lambda _: Agent[sid].set_config_option("model", "large"),
        )
    )
    options, _ = await run(body)
    assert {o["id"]: o["current_value"] for o in options} == {"model": "large", "fast": True}


async def test_an_unknown_config_option_raises():
    body = with_session(lambda sid: Agent[sid].set_config_option("colour", "red"))
    with pytest.raises(AcpError, match=r"Invalid params \(-32602\)") as caught:
        await run(body)
    assert caught.value.code == -32602


async def test_set_mode_reaches_the_agent():
    body = with_session(
        lambda sid: nu.Sequential(Agent[sid].set_mode("plan"), log_all(Agent[sid].prompt("stats")))
    )
    _, log = await run(body)
    assert stats_of(log["a"])["modes"] == {"s1": "plan"}


# --- updates() ------------------------------------------------------------------------


async def test_updates_fan_out_to_every_reader_inside_and_between_turns():
    fabric, sid = await _fabric()
    try:
        first, second = fabric.updates(sid), fabric.updates(sid)
        turns = [item async for item in fabric.prompt(sid, "hello")]
        turns += [item async for item in fabric.prompt(sid, "later")]
        # A loop, not a nested comprehension: Python 3.10 refuses await in the inner one.
        heard = []
        for reader in (first, second):
            heard.append([await asyncio.wait_for(anext(reader), 5) for _ in range(3)])
        kinds = ["agent_message_chunk", "agent_message_chunk", "session_info_update"]
        assert [u["session_update"] for u in heard[0]] == kinds
        assert heard[0] == heard[1]
        # The responses belong to the prompt streams, never to updates().
        assert [t["stop_reason"] for t in turns if "stop_reason" in t] == ["end_turn", "end_turn"]
        await first.aclose()
        await second.aclose()
        assert fabric._sessions[sid].subscribers == set()
    finally:
        await fabric.acleanup()


async def test_updates_only_hear_their_own_session():
    fabric, s1 = await _fabric()
    try:
        s2 = (await fabric.new_session(None, None, None, None))["session_id"]
        heard = fabric.updates(s1)
        [item async for item in fabric.prompt(s2, "hello")]
        [item async for item in fabric.prompt(s1, "probe")]
        # s2's two chunks came first on the wire; s1's reader hears only its own.
        assert texts([await asyncio.wait_for(anext(heard), 5)]) == ["1"]
        await heard.aclose()
    finally:
        await fabric.acleanup()


async def test_updates_end_when_the_fabric_closes():
    fabric, sid = await _fabric()
    heard = fabric.updates(sid)
    await fabric.acleanup()
    assert [item async for item in heard] == []
