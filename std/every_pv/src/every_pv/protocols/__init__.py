"""PV-specific protocols for capability checking.

This module provides runtime-checkable protocols for PV refs.
"""

from .capabilities import (
    PVClearable,
    PVDeletable,
    PVExistable,
    PVExtractable,
    PVGettable,
    PVLengthable,
    PVSettable,
    PVStorable,
)


__all__ = [
    "PVClearable",
    "PVDeletable",
    "PVExistable",
    "PVExtractable",
    "PVGettable",
    "PVLengthable",
    "PVSettable",
    "PVStorable",
]
