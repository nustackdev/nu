"""Cache headers on the SPA mount: a release shows up without a hard reload.

Hashed ``assets/`` files are cached for good, since a new build is a new name.
index.html, the deep-URL fallback and the unhashed files are revalidated on
every load, so the browser always picks up the newest index and its assets.
"""

from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient

from nustd.ws_server.fabric import _SPAStatic


@pytest.fixture
def client(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html></html>")
    (tmp_path / "assets" / "index-abc123.js").write_text("export {}")
    (tmp_path / "favicon-32.png").write_bytes(b"png")
    app = Starlette(routes=[Mount("/", app=_SPAStatic(directory=tmp_path, html=True))])
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize("url", ["/", "/index.html", "/some/deep/page", "/favicon-32.png"])
def test_index_and_unhashed_files_revalidate(client, url):
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"


def test_hashed_assets_are_immutable(client):
    response = client.get("/assets/index-abc123.js")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_missing_asset_falls_back_to_a_revalidated_index(client):
    response = client.get("/assets/gone-old.js")
    assert "text/html" in response.headers["content-type"]
    assert response.headers["cache-control"] == "no-cache"


def test_revalidation_answers_304_with_the_header(client):
    etag = client.get("/").headers["etag"]
    response = client.get("/", headers={"if-none-match": etag})
    assert response.status_code == 304
    assert response.headers["cache-control"] == "no-cache"
