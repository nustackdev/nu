"""nustd.webbrowser: tabs open through the bound browser, and wait for a server first."""

from __future__ import annotations

import asyncio
from typing import ClassVar

import nu
import nustd.webbrowser as webbrowser


class Seen(webbrowser.Browser):
    """A browser that records the urls it is asked to open, and opens none."""

    urls: ClassVar[list[str]] = []

    def open(self, url: str) -> None:
        Seen.urls.append(url)


def _bound(body: nu.Nu) -> nu.Nu:
    Seen.urls = []
    return nu.Provide(Seen, kwargs={}, body=body)


def test_open_goes_through_the_bound_browser():
    nu.run(_bound(webbrowser.BROWSER.open("http://example.test/")))
    assert Seen.urls == ["http://example.test/"]


def test_open_async_goes_through_the_bound_browser():
    asyncio.run(nu.arun(_bound(webbrowser.BROWSER.open("http://example.test/a"))))
    assert Seen.urls == ["http://example.test/a"]


def test_listening_sees_a_server():
    async def main():
        server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server:
            up = await webbrowser.listening("127.0.0.1", port)
        down = await webbrowser.listening("127.0.0.1", port)
        return up, down

    assert asyncio.run(main()) == (True, False)


def test_tab_opened_once_the_server_answers():
    async def main():
        server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server:
            url = f"http://127.0.0.1:{port}/"
            await nu.arun(_bound(webbrowser.tab_opened(url, "127.0.0.1", port, timeout=5)))
        return url

    url = asyncio.run(main())
    assert Seen.urls == [url]


def test_tab_opened_gives_up_quietly():
    asyncio.run(nu.arun(_bound(webbrowser.tab_opened("http://x/", "127.0.0.1", 1, timeout=0.3))))
    assert Seen.urls == []
