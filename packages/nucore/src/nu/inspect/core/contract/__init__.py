"""The docstring contract: what a written fact may not lie about.

Sits between the readers and the kinds. Knows the contract and nothing else:
not Nu, not what an interaction is. Shared by every kind, which is what stops
each one re-deriving the same rules.

- ``sections`` names the sections, once.
- ``call`` merges the two sources into the call form.
- ``check`` is one law per section, returning violations rather than raising.
  Absence of a section is not a violation; it is empty data on the record.
"""

from __future__ import annotations

from nu.inspect.core.contract.call import Arg, call_form
from nu.inspect.core.contract.check import (
    SUMMARY_LIMIT,
    Violation,
    check_args,
    check_example,
    check_summary,
)
from nu.inspect.core.contract.sections import ARGS, EXAMPLE, NOTES, YIELDS


__all__ = [
    "ARGS",
    "EXAMPLE",
    "NOTES",
    "SUMMARY_LIMIT",
    "YIELDS",
    "Arg",
    "Violation",
    "call_form",
    "check_args",
    "check_example",
    "check_summary",
]
