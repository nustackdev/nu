"""Backend-specific types."""

from __future__ import annotations

from typing import Literal


# ========================================================
# Storage-specific types
# ========================================================


type StorageMode = Literal["read", "write"]
