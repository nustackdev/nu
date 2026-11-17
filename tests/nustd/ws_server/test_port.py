"""The port: a given one that is taken is PortTaken before uvicorn starts; none, the first free one."""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING

import pytest

from nustd.ws_server import PortTaken, WebServer, fabric


if TYPE_CHECKING:
    from collections.abc import Iterator


class _Session:
    async def run_intake(self) -> None:
        return None


@pytest.fixture
def held() -> Iterator[int]:
    """A port some other socket is listening on for the test's length."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        yield s.getsockname()[1]


async def test_a_taken_port_is_refused_before_the_server_starts(held: int):
    web = WebServer(session_cls=_Session, port=held, open_browser=False)
    with pytest.raises(PortTaken, match=f"Port {held} on 127.0.0.1 is taken"):
        await web.asetup(None)  # type: ignore[arg-type]
    assert web._server is None


def test_no_port_skips_a_taken_one(held: int, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fabric, "DEFAULT_PORT", held)
    assert fabric._pick_port("127.0.0.1", None) > held


def test_no_free_port_in_the_scan_is_refused(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fabric, "_bindable", lambda host, port: False)
    with pytest.raises(PortTaken, match="No free port"):
        fabric._pick_port("127.0.0.1", None)


def test_a_free_given_port_is_kept():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        free = s.getsockname()[1]
    assert fabric._pick_port("127.0.0.1", free) == free
