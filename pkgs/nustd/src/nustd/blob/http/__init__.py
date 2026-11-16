"""Blob stores in the browser: where a server serves one, and the urls the leaves draw from.

A blob store (``nustd.blob``) stores and returns bytes and knows no urls. A
``BlobMount`` says where a web server serves one: the url an image, a video
or a download reads, and the url an upload POSTs to. It is a plain value, so
a program builds urls with it in any process, server or not::

    Files = nustd.blob.StoreRef("files")
    files = nustd.blob.http.BlobMount("/files")

    nustd.ui.ImageRef("pic").set(files.url(bid))

The server half is ``serve_blobs`` (``nustd.blob.http.serving``, loaded on
first use, as it needs Starlette): the routes over each mount, and the
brackets holding each store's backend open while the server runs.
``nustd.ui.serve`` takes the same pairs as ``blobs=``::

    spec = nustd.blob.lmdb(Files, ".store/files")
    nustd.ui.serve(program, blobs={files: spec})   # the server: GET and POST under /files
    nu.With(spec, body=...)                         # a run: the same store
"""

from __future__ import annotations

import importlib
import re
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu.lang import Nu, StrArg

    from .serving import serve_blobs


__all__ = ["BlobMount", "serve_blobs"]


_PATH = re.compile(r"(/[A-Za-z0-9_.~-]+)+")


class BlobMount:
    """Where a web server serves one blob store, and the urls that reach it.

    ``GET {at}/<id>`` serves a blob, ``POST {at}`` takes an upload. The mount
    is only the place and its rules; which store sits there is the server's
    say (``serve_blobs``).

    Args:
        at: the path the store sits under: one or more segments, starting
            with ``/`` and not ending with one.
        max_upload: the most bytes one upload may hold; a bigger one gets 413
            and stores nothing. None leaves only the backend's own cap.
        cross_site: take uploads from pages on other sites too. Off, a POST
            that a browser says came from another site gets 403: a page the
            user has open elsewhere cannot fill the store.

    Notes:
        - Every blob is write-once under its id, so a url never changes what
          it serves and is cached forever.
        - A stored mime is served as given. A mount taking uploads from
          untrusted users serves their ``text/html`` or SVG inline from this
          origin, so put such a store behind its own origin or check the mime.

    Example:
        files = nustd.blob.http.BlobMount("/files", max_upload=1 << 30)
        files.url("0123456789abcdef0123456789abcdef")    # "/files/0123...ef"
    """

    __slots__ = ("at", "cross_site", "max_upload")

    def __init__(self, at: str, *, max_upload: int | None = None, cross_site: bool = False) -> None:
        if (
            not isinstance(at, str)
            or _PATH.fullmatch(at) is None
            or any(seg in (".", "..") for seg in at.split("/"))
        ):
            msg = (
                f"a mount is a path like '/files': segments after '/', no trailing '/', got {at!r}"
            )
            raise ValueError(msg)
        if max_upload is not None and (
            not isinstance(max_upload, int) or isinstance(max_upload, bool) or max_upload < 0
        ):
            raise ValueError(f"max_upload is a byte count, 0 or more, got {max_upload!r}")
        self.at = at
        self.max_upload = max_upload
        self.cross_site = cross_site

    def url(self, blob_id: StrArg, *, download: bool = False) -> str | Nu[str]:
        """Where the browser reads the blob: ``{at}/<id>``.

        A ``str`` id gives a ``str`` at once, checked to be an id, ready for a
        ``src=``. A term id, such as a put's, gives a term that yields the
        ``str`` when it runs; the id it yields is not checked there.

        Args:
            blob_id: the blob's id.
            download: ask the browser to save it under its name rather than
                show it (``?download=1``), for a link or a button's ``href``.
        """
        from nu.lang import Nu
        from nustd.blob._base import check_id

        prefix = f"{self.at}/"
        suffix = "?download=1" if download else ""
        if isinstance(blob_id, Nu):
            from nu.core import Add

            return Add(Add(prefix, blob_id), suffix) if suffix else Add(prefix, blob_id)
        return prefix + check_id(blob_id) + suffix

    def upload_url(self) -> str:
        """Where an upload POSTs: ``{at}``."""
        return self.at

    def __repr__(self) -> str:
        return f"BlobMount({self.at!r})"


def __getattr__(name: str) -> object:
    """``serve_blobs`` on first access: it needs Starlette, ``BlobMount`` does not."""
    if name != "serve_blobs":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = importlib.import_module(".serving", __name__).serve_blobs
    globals()[name] = value
    return value
