"""eb-tree-view: Interactive HTML tree explorer for everybase."""

from __future__ import annotations

import json
import tempfile
import webbrowser
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

from .serialize import serialize


if TYPE_CHECKING:
    from everybase.tree import Node


__all__ = [
    "open_in_browser",
    "render_html",
]


def render_html(root: Node, *, title: str = "everybase tree explorer") -> str:
    """Serialize tree and embed in HTML template. Returns complete HTML string."""
    data = serialize(root)
    template = files("eb_tree_view").joinpath("template.html").read_text(encoding="utf-8")
    tree_json = json.dumps(data, indent=2)
    html = template.replace("__TREE_DATA__", tree_json)
    html = html.replace("__TREE_TITLE__", title)
    return html


def open_in_browser(root: Node, *, title: str = "everybase tree explorer") -> Path:
    """Write HTML to temp file, open in default browser. Returns path."""
    html = render_html(root, title=title)
    tmp = tempfile.NamedTemporaryFile(
        suffix=".html",
        prefix="eb-tree-",
        delete=False,
    )
    tmp.write(html.encode("utf-8"))
    tmp.close()
    path = Path(tmp.name)
    webbrowser.open(path.as_uri())
    return path
