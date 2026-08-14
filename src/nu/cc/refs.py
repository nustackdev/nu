"""PromptRef: Ref addressing a Claude Code prompt endpoint on a Service.

Mirrors nu.http verb refs: `.method(**defaults)` returns a Method declaration
that the ServiceMeta descriptor unwraps at class access; calling the Ref with
kwargs produces a CCPrompt interaction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.service import Method, MethodRef
from nu.forms import Dict

from .interactions import CCPrompt


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["PromptRef"]


class PromptRef(MethodRef):
    """Claude Code prompt endpoint Ref."""

    @classmethod
    def method(cls, **defaults: object) -> PromptRef:  # type: ignore[override]
        """Declare a prompt endpoint. Defaults merge with per-call overrides."""
        return Method(cls, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, prompt: object, **overrides: object) -> Nu:
        """Run one prompt turn; kwargs override the endpoint defaults."""
        return CCPrompt(self, Dict.of(prompt=prompt, **overrides))
