"""The upload errors: one per failure code the tab answers.

``UploadError`` and its subclasses, the code each one stands for, and the
message a read raises with. The refs, the reads and any host share them, so
an app catches one thing wherever the read ran.
"""

from __future__ import annotations

from typing import Any, ClassVar


__all__ = [
    "FileGone",
    "NoFile",
    "UploadCanceled",
    "UploadError",
    "UploadFailed",
    "UploadRefused",
    "UploadTooLarge",
]


class UploadError(Exception):
    """A read or a pull on an upload ref that could not be served.

    The base of every upload failure, so an app catches one thing. ``code``
    is what the tab answered (``no_file``, ``unreadable``, ``canceled``,
    ``too_large``, ``refused``, ``network``).
    """

    code: ClassVar[str] = ""


class NoFile(UploadError):  # noqa: N818 - a state, not an error kind
    """Nothing is picked: the input is empty, or the entry is not there."""

    code = "no_file"


class FileGone(UploadError):  # noqa: N818 - a state, not an error kind
    """The file changed or moved on disk after the pick, so the tab cannot read it.

    The input keeps the file with ``state: "failed"`` and ``error:
    "unreadable"`` and asks the person to pick it again.
    """

    code = "unreadable"


class UploadCanceled(UploadError):  # noqa: N818 - a state, not an error kind
    """The transfer was canceled, by ``cancel()`` or by the person."""

    code = "canceled"


class UploadTooLarge(UploadError):  # noqa: N818 - a state, not an error kind
    """The bytes are over the intake's cap, so the server refused them (413)."""

    code = "too_large"


class UploadRefused(UploadError):  # noqa: N818 - a state, not an error kind
    """The server refused the transfer, or a token names nothing on the server.

    A tab that is not live, a token that was dropped or swept, or one that
    does not resolve inside the tab's own dir.
    """

    code = "refused"


class UploadFailed(UploadError):  # noqa: N818 - a state, not an error kind
    """The transfer broke on the way: a network drop mid POST."""

    code = "network"


_ERRORS: dict[str, type[UploadError]] = {
    cls.code: cls
    for cls in (NoFile, FileGone, UploadCanceled, UploadTooLarge, UploadRefused, UploadFailed)
}

_MESSAGES = {
    "no_file": "no file is picked",
    "unreadable": "the file changed or moved on disk after it was picked; pick it again",
    "canceled": "the transfer was canceled",
    "too_large": "the file is over the server's upload cap",
    "refused": "the server refused the transfer",
    "network": "the transfer broke on the way",
}


def _error(code: str, where: str) -> UploadError:
    """The error for ``code``, its message naming the ref at ``where``."""
    cls = _ERRORS.get(code, UploadFailed)
    reason = _MESSAGES.get(code, f"the transfer failed ({code})")
    return cls(f"{where}: {reason}")


def _check_answer(answer: dict[str, Any], where: str) -> str:
    """The token an answer names, or the error it reports, raised."""
    code = answer.get("error") or ""
    if not code and answer.get("state") == "canceled":
        code = "canceled"
    if code:
        raise _error(str(code), where)
    token = answer.get("token")
    if not isinstance(token, str) or not token:
        raise UploadRefused(f"{where}: the tab answered with no file")
    return token
