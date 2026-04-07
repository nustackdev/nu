"""Shapes tree utilities - ref chain deformation and annotation."""

from .annotate import annotate_ref_loads
from .deform import extract_static_address, reconstruct_with_flat_ref, walk_ref_chain

__all__ = [
    "annotate_ref_loads",
    "extract_static_address",
    "reconstruct_with_flat_ref",
    "walk_ref_chain",
]
