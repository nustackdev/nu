"""CodeBlockRef: preformatted code block with optional language label. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import DictForm

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["CodeBlockRef"]


class CodeBlockRef(NudleRef):
    """Display-only code block. One `write` op carries a partial dict of {code, language, show_copy}."""

    code: ClassVar[str] = ""
    language: ClassVar[str] = ""
    show_copy: ClassVar[bool] = True

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        props: dict[str, object] = {}
        if cls.code != "":
            props["code"] = cls.code
        if cls.language != "":
            props["language"] = cls.language
        if cls.show_copy is not True:
            props["show_copy"] = cls.show_copy
        return props

    def store(
        self,
        code: Nu | str | None = None,
        language: Nu | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if code is not None:
            payload["code"] = code
        if language is not None:
            payload["language"] = language
        return Write(self, DictForm.of(**payload))

    def store_code(self, code: Nu | str) -> Nu:
        return Write(self, DictForm.of(code=code))

    def store_language(self, language: Nu | str) -> Nu:
        return Write(self, DictForm.of(language=language))
