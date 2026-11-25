"""nustd.ui.uploads -- every part of a picked file's trip from tab to program.

A file the person picks in the browser stays there until the program asks
for bytes. Then the browser POSTs them on a second connection beside the ws,
into a temp area the host owns, and the program hears a token back over the
ws. Bytes never ride the ws and the browser never learns a server path.

All of it lives here; a host (nudle, nuspace) only assembles it.

- ``area``         -- ``UploadArea``, the temp folder and its lifecycle, and
                      ``UploadView``, one tab's resolve only view of it.
- ``intake``       -- the ``POST /_nu/upload/{sid}`` route that fills the area.
- ``interactions`` -- the commands a program sends a tab (``Pull``, ``Slice``,
                      ``Cancel``, ``Discard``, ``RemoveFile``) and the reads
                      (``ReadSlice``, ``ReadBytes``, ``OpenFile``).
- ``errors``       -- ``UploadError`` and its subclasses, one per failure code.
- ``presets``      -- ``uploads``, the area's bracket and route as one pair,
                      and ``upload_view``, binding each arm its tab's view.

The refs that hand these out are in ``nustd.ui.refs``. Importing this package
never loads a web server: starlette is ``intake``'s alone, and ``uploads``
imports it only when it builds the route.
"""

from __future__ import annotations

from .area import (
    STALE_AFTER,
    UPLOAD_PREFIX,
    UploadArea,
    UploadView,
    check_sid,
    check_token,
    tab_dir,
    upload_file,
)
from .errors import (
    FileGone,
    NoFile,
    UploadCanceled,
    UploadError,
    UploadFailed,
    UploadNoSpace,
    UploadRefused,
    UploadTooLarge,
)
from .interactions import (
    BYTES_WARN,
    STEP,
    Cancel,
    Discard,
    OpenFile,
    Pull,
    ReadBytes,
    ReadSlice,
    RemoveFile,
    Slice,
)
from .presets import UploadViewFor, upload_view, uploads


__all__ = [
    "BYTES_WARN",
    "STALE_AFTER",
    "STEP",
    "UPLOAD_PREFIX",
    "Cancel",
    "Discard",
    "FileGone",
    "NoFile",
    "OpenFile",
    "Pull",
    "ReadBytes",
    "ReadSlice",
    "RemoveFile",
    "Slice",
    "UploadArea",
    "UploadCanceled",
    "UploadError",
    "UploadFailed",
    "UploadNoSpace",
    "UploadRefused",
    "UploadTooLarge",
    "UploadView",
    "UploadViewFor",
    "check_sid",
    "check_token",
    "tab_dir",
    "upload_file",
    "upload_view",
    "uploads",
]
