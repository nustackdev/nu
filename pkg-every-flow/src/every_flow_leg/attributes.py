"""Attribute-related primitives.

This module provides basic flows to manage local attribites:
- SetAttr: Stores given data point as an attribute
"""

from __future__ import annotations

import attrs

from everybase import Flow, Runtime, Term


__all__ = [
    "SetAttr",
]


@attrs.define
class _SetAttr[RuntimeT: Runtime](Flow[RuntimeT]):
    """Set attribute."""

    key: Term | str = attrs.field()
    value: Term | object = attrs.field()
    child: Term | Flow = attrs.field()
    step_name: Term | str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute children sequentially."""
        key = self._resolve_str(runtime, self.key)
        step_name = (
            self._resolve_str(runtime, self.step_name) if self.step_name is not None else None
        )
        if isinstance(self.value, Term):
            value = runtime.terms.execute_term(self.value)
        else:
            value = self.value

        runtime.attributes.set(runtime.path, key, value, step_name=step_name)  # type: ignore

        await self.execute_child(self.child, 0, runtime)

    def _resolve_str(self, runtime: RuntimeT, value: Term | str) -> str:
        """Resolve Term or str to str."""
        if isinstance(value, Term):
            result = runtime.terms.execute_term(value)
            if not isinstance(result, str):
                raise ValueError(f"Expected str, got {type(result)}")
            return result
        return value


def SetAttr(key: Term | str, value: object, step_name: Term | str, child: Term | Flow) -> _SetAttr:  # noqa: N802
    """Set attribute."""
    return _SetAttr(key, value, child, step_name)
