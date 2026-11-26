"""Permission requests in ``nustd.acp``: answered by the bind's policy, or asked and answered.

The scripted Agent's ``perm`` turn asks once (allow, always, reject) and then
says what it was answered; ``perm-reject`` offers only a reject option;
``late`` asks 0.2s after its ``go`` chunk, so a cancel sent on ``go`` crosses
the request on the wire.
"""

from __future__ import annotations

import inspect

import pytest
from _support.acp_fixtures import Agent, Log, has, run, texts

import nu


pytestmark = pytest.mark.timeout(20, method="thread")


def with_session(body):
    (name,) = inspect.signature(body).parameters
    return nu.let(body, **{name: nu.Dict(Agent.new_session())["session_id"]})


def log_all(stream, into=Log.a):
    return nu.ForEachDo(stream, into.append)


def is_chunk(item, text):
    return nu.And(
        has(item, "session_update"),
        nu.Dict(item)["session_update"] == "agent_message_chunk",
        nu.Dict(nu.Dict(item)["content"])["text"] == text,
    )


def answering(sid, option_id):
    """Log every item; answer a permission request with ``option_id``."""
    return lambda item: nu.Sequential(
        Log.a.append(item),
        nu.IfDo(
            has(item, "request_permission"),
            Agent[sid].answer_permission(nu.Dict(item)["request_permission"], option_id),
        ),
    )


def on_go(sid, act):
    """Log every item; run ``act`` on the ``go`` chunk of a ``late`` turn."""
    return lambda item: nu.Sequential(Log.a.append(item), nu.IfDo(is_chunk(item, "go"), act))


async def test_the_default_policy_rejects_once_and_collect_never_stalls():
    body = with_session(lambda sid: log_all(Agent[sid].prompt("perm")))
    _, log = await run(body)
    assert texts(log["a"]) == ["selected:reject"]
    assert log["a"][-1] == {"stop_reason": "end_turn"}


@pytest.mark.parametrize(
    ("policy", "prompt", "answer"),
    [
        ("allow_once", "perm", "selected:allow"),
        ("allow_always", "perm", "selected:always"),
        ("reject_once", "perm", "selected:reject"),
        # No reject_always offered: the other reject kind stands in.
        ("reject_always", "perm", "selected:reject"),
        # No allow option at all: the request is answered cancelled.
        ("allow_once", "perm-reject", "cancelled"),
    ],
)
async def test_a_policy_answers_inside_the_fabric(policy, prompt, answer):
    body = with_session(lambda sid: log_all(Agent[sid].prompt(prompt)))
    _, log = await run(body, permissions=policy)
    assert texts(log["a"]) == [answer]
    assert not any("request_permission" in item for item in log["a"])


async def test_ask_yields_the_request_and_waits_for_its_answer():
    body = with_session(
        lambda sid: nu.ForEachDo(Agent[sid].prompt("perm"), answering(sid, "always"))
    )
    _, log = await run(body, permissions="ask")
    keys = {"session_update", "request_permission", "stop_reason"}
    kinds = [next(iter(set(item) & keys)) for item in log["a"]]
    assert kinds == ["session_update", "request_permission", "session_update", "stop_reason"]
    request = log["a"][1]
    assert isinstance(request["request_permission"], int)
    assert request["tool_call"] == {"tool_call_id": "t1"}
    assert [o["option_id"] for o in request["options"]] == ["allow", "always", "reject"]
    assert request["options"][0] == {"option_id": "allow", "name": "Allow", "kind": "allow_once"}
    assert texts(log["a"]) == ["selected:always"]
    assert log["a"][-1] == {"stop_reason": "end_turn"}


async def test_a_parallel_arm_answers_through_updates():
    body = with_session(
        lambda sid: nu.Race(
            nu.ForEachDo(
                Agent[sid].updates(),
                lambda item: nu.IfDo(
                    has(item, "request_permission"),
                    Agent[sid].answer_permission(nu.Dict(item)["request_permission"], "reject"),
                ),
            ),
            log_all(Agent[sid].prompt("perm"), Log.b),
        )
    )
    _, log = await run(body, permissions="ask")
    assert any("request_permission" in item for item in log["b"])
    assert texts(log["b"]) == ["selected:reject"]
    assert log["b"][-1] == {"stop_reason": "end_turn"}


@pytest.mark.parametrize("act", ["cancel", "close"])
async def test_cancel_and_close_answer_pending_requests_with_cancelled(act):
    def body(sid):
        stop = Agent[sid].cancel() if act == "cancel" else Agent[sid].close()
        return nu.ForEachDo(
            Agent[sid].prompt("perm"),
            lambda item: nu.Sequential(
                Log.a.append(item),
                nu.IfDo(has(item, "request_permission"), stop),
            ),
        )

    _, log = await run(with_session(body), permissions="ask")
    assert texts(log["a"]) == ["cancelled"]
    stop_reason = "cancelled" if act == "cancel" else "end_turn"
    assert log["a"][-1] == {"stop_reason": stop_reason}


@pytest.mark.parametrize("policy", ["ask", "allow_once"])
@pytest.mark.parametrize("act", ["cancel", "close"])
async def test_a_request_crossing_a_cancel_is_answered_cancelled(policy, act):
    # Under ask nothing would ever answer it; under a policy it would be approved.
    def body(sid):
        stop = Agent[sid].cancel() if act == "cancel" else Agent[sid].close()
        return nu.ForEachDo(Agent[sid].prompt("late"), on_go(sid, stop))

    _, log = await run(with_session(body), permissions=policy)
    assert texts(log["a"]) == ["go", "cancelled"]
    assert not any("request_permission" in item for item in log["a"])


async def test_a_new_turn_after_a_cancel_asks_again():
    body = with_session(
        lambda sid: nu.Sequential(
            nu.ForEachDo(Agent[sid].prompt("late"), on_go(sid, Agent[sid].cancel())),
            nu.ForEachDo(Agent[sid].prompt("perm"), lambda item: Log.b.append(item)),
        )
    )
    _, log = await run(body, permissions="allow_once")
    assert texts(log["b"]) == ["selected:allow"]


async def test_an_answer_after_cancel_is_left_alone():
    body = with_session(
        lambda sid: nu.ForEachDo(
            Agent[sid].prompt("perm"),
            lambda item: nu.Sequential(
                Log.a.append(item),
                nu.IfDo(
                    has(item, "request_permission"),
                    nu.Sequential(
                        Agent[sid].cancel(),
                        Agent[sid].answer_permission(nu.Dict(item)["request_permission"], "allow"),
                    ),
                ),
            ),
        )
    )
    _, log = await run(body, permissions="ask")
    assert texts(log["a"]) == ["cancelled"]


async def test_an_option_the_request_did_not_offer_raises():
    body = with_session(
        lambda sid: nu.ForEachDo(Agent[sid].prompt("perm"), answering(sid, "maybe"))
    )
    with pytest.raises(ValueError, match="offers allow, always, reject, not 'maybe'"):
        await run(body, permissions="ask")
