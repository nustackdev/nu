"""The docstring contract: what must be written, and whether it was.

Sits between the readers and the kinds. It knows the contract and nothing
else: not Nu, not what an interaction is. Everything here is shared by every
kind, which is what stops five packages re-deriving the same rules.

- ``sections`` names the six sections, once.
- ``guide`` is the shared half of the contract as text.
- ``call`` merges the two sources into the call form.
- ``check`` is one checker per section, returning problems rather than raising.
"""

from __future__ import annotations

from nu.info.core.contract.call import Arg, call_form
from nu.info.core.contract.check import (
    SUMMARY_LIMIT,
    Problem,
    check_args,
    check_example,
    check_summary,
    check_yields,
)
from nu.info.core.contract.guide import SECTIONS
from nu.info.core.contract.sections import ARGS, EXAMPLE, NOTES, YIELDS


__all__ = [
    "ARGS",
    "EXAMPLE",
    "NOTES",
    "SECTIONS",
    "SUMMARY_LIMIT",
    "YIELDS",
    "Arg",
    "Problem",
    "call_form",
    "check_args",
    "check_example",
    "check_summary",
    "check_yields",
]
