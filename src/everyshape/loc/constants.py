"""Constants."""

from __future__ import annotations


__all__ = [
    "DATA_ROOT",
    "METADATA_ROOT",
]

# Root marker for the root data segment (stores actual data)
DATA_ROOT: str = "/"
# Root marker for the metadata segment (stores metadata)
METADATA_ROOT: str = "/m"
