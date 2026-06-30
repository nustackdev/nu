"""Runtime utilities: the drive loop and the per-execution Budget.

Pieces the Runtime owns but that aren't the headline surface a user reaches
for: lifecycle helpers (``into_loop``, ``safely_(a)closing``) and the
per-call resource bag (``Budget``).
"""

from __future__ import annotations

from .budget import Budget
from .loop import into_loop, safely_aclosing, safely_closing


__all__ = [
    "Budget",
    "into_loop",
    "safely_aclosing",
    "safely_closing",
]
