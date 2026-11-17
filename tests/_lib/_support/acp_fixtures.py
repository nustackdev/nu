"""Shared pieces for the ``nustd.acp`` tests: the fake Agent's bind, a log Shape, runners."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import nu
import nustd.acp


__all__ = ["FAKE", "Agent", "Log", "bound", "has", "run", "stats_of", "texts"]


#: The scripted Agent (``acp_agent.py``), run by this interpreter.
FAKE = [sys.executable, str(Path(__file__).with_name("acp_agent.py"))]

Agent = nustd.acp.AgentRef("fake")


class Log(nu.Shape):
    """Where a test's streams land: three lists of items, read back as a plain dict."""

    a = nu.ListRef.slot(dict)
    b = nu.ListRef.slot(dict)
    c = nu.ListRef.slot(dict)


def bound(body: nu.Nu, **bind: Any) -> nu.Nu:
    """``body`` with the fake Agent bound."""
    return nu.With(nustd.acp.bind(Agent, command=FAKE, **bind), body=body)


async def run(body: nu.Nu, **bind: Any) -> tuple[object, dict[str, list]]:
    """Run ``body`` with the fake bound; its value and what landed in ``Log``."""
    data: dict[str, list] = {"a": [], "b": [], "c": []}
    ctx = nu.Context().bind(dict, data, Log)
    value, _ = await nu.arun(bound(body, **bind), ctx)
    return value, data


def has(item: nu.Nu, key: str) -> nu.Nu:
    """Whether a stream item carries ``key``: told apart by key, as the fabric shapes them."""
    return nu.Contains(item, key)


def texts(items: list[dict]) -> list[str]:
    """The text of every ``agent_message_chunk`` among ``items``."""
    return [
        item["content"]["text"]
        for item in items
        if item.get("session_update") == "agent_message_chunk"
    ]


def stats_of(items: list[dict]) -> dict[str, Any]:
    """The fake Agent's record, from the items of a ``stats`` prompt."""
    return json.loads(texts(items)[0])
