"""Functional tests for nu.http: HttpFabric + 5 verb interactions + bind.

httpx is an optional dependency (`nustack-py[http]`), so the whole file is
skipped when it is not importable. A single `httpx.MockTransport` is injected
by monkey-patching `httpx.AsyncClient` inside `nu.http.fabric`, so the real
HTTP stack (routing, request formatting, response parsing) runs end-to-end
against a mock server that never touches the network.
"""

from __future__ import annotations

import pytest


httpx = pytest.importorskip("httpx")

import nu  # noqa: E402


# --- MockTransport wiring ---------------------------------------------------


def _make_handler(recorder: list[httpx.Request]):
    def handler(request: httpx.Request) -> httpx.Response:
        recorder.append(request)
        path = request.url.path
        if path == "/repos/nu/core":
            return httpx.Response(200, json={"name": "core", "stars": 42})
        if path == "/echo":
            body = None
            if request.content:
                import json as _json

                body = _json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "method": request.method,
                    "query": dict(request.url.params),
                    "body": body,
                },
            )
        if path == "/items/7":
            return httpx.Response(200, json={"id": 7, "deleted": True})
        return httpx.Response(404, json={"error": "not found"})

    return handler


@pytest.fixture
def calls() -> list[httpx.Request]:
    return []


@pytest.fixture(autouse=True)
def _patch_httpx_client(monkeypatch, calls):
    """Force every AsyncClient the fabric opens to use MockTransport."""
    transport = httpx.MockTransport(_make_handler(calls))
    real = httpx.AsyncClient

    class _Client(real):
        def __init__(self, **kw):
            kw.setdefault("transport", transport)
            super().__init__(**kw)

    monkeypatch.setattr("nu.http.fabric.httpx.AsyncClient", _Client)


# --- verb dispatch ----------------------------------------------------------


class GH(nu.Service):
    get_repo = nu.http.GETRef.method("/repos/{owner}/{name}")
    echo_get = nu.http.GETRef.method("/echo")
    echo_post = nu.http.POSTRef.method("/echo")
    echo_put = nu.http.PUTRef.method("/echo")
    echo_patch = nu.http.PATCHRef.method("/echo")
    delete_item = nu.http.DELETERef.method("/items/{id}")


@pytest.fixture
def app():
    def make(body):
        return nu.With(
            nu.http.bind(GH, base_url="https://api.example.com"),
            body=body,
        )

    return make


@pytest.mark.asyncio
async def test_get_formats_path_and_parses_json(app, calls):
    value, _ = await nu.arun(app(GH.get_repo(owner="nu", name="core")))
    assert value == {"name": "core", "stars": 42}
    assert calls[-1].method == "GET"
    assert calls[-1].url.path == "/repos/nu/core"


@pytest.mark.asyncio
async def test_get_extra_kwargs_go_to_query_string(app, calls):
    value, _ = await nu.arun(app(GH.echo_get(page=2, q="foo")))
    assert value["query"] == {"page": "2", "q": "foo"}
    assert calls[-1].url.params.get("page") == "2"


@pytest.mark.asyncio
async def test_post_body_is_sent_as_json(app, calls):
    value, _ = await nu.arun(app(GH.echo_post(name="x", tags=[1, 2])))
    assert value["method"] == "POST"
    assert value["body"] == {"name": "x", "tags": [1, 2]}


@pytest.mark.asyncio
async def test_put_body_is_sent_as_json(app, calls):
    value, _ = await nu.arun(app(GH.echo_put(v=1)))
    assert value["method"] == "PUT"
    assert value["body"] == {"v": 1}


@pytest.mark.asyncio
async def test_patch_body_is_sent_as_json(app, calls):
    value, _ = await nu.arun(app(GH.echo_patch(v=1)))
    assert value["method"] == "PATCH"


@pytest.mark.asyncio
async def test_delete_formats_path_and_returns_json(app, calls):
    value, _ = await nu.arun(app(GH.delete_item(id=7)))
    assert value == {"id": 7, "deleted": True}
    assert calls[-1].method == "DELETE"
    assert calls[-1].url.path == "/items/7"


@pytest.mark.asyncio
async def test_declaration_defaults_flow_into_body(app, calls):
    class Svc(nu.Service):
        echo = nu.http.POSTRef.method("/echo", version=1, source="test")

    tree = nu.With(
        nu.http.bind(Svc, base_url="https://api.example.com"),
        body=Svc.echo(payload=[1, 2, 3]),
    )
    value, _ = await nu.arun(tree)
    assert value["body"] == {"version": 1, "source": "test", "payload": [1, 2, 3]}


@pytest.mark.asyncio
async def test_non_2xx_raises_http_status_error(app):
    class Svc(nu.Service):
        missing = nu.http.GETRef.method("/nope")

    tree = nu.With(
        nu.http.bind(Svc, base_url="https://api.example.com"),
        body=Svc.missing(),
    )
    with pytest.raises(httpx.HTTPStatusError):
        await nu.arun(tree)


@pytest.mark.asyncio
async def test_bind_tags_by_service_class(calls):
    class SvcA(nu.Service):
        one = nu.http.GETRef.method("/repos/nu/core")

    class SvcB(nu.Service):
        one = nu.http.GETRef.method("/echo")

    tree = nu.With(
        nu.http.bind(SvcA, base_url="https://a.example.com"),
        nu.http.bind(SvcB, base_url="https://b.example.com"),
        body=SvcA.one(),
    )
    value, _ = await nu.arun(tree)
    assert value == {"name": "core", "stars": 42}
    # Only SvcA's fabric fired; SvcB was bound but not called.
    assert str(calls[-1].url).startswith("https://a.example.com")
