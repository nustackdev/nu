"""everyshape.meta — shared utilities for substrate-specific tree deformations."""

from everybase.shape.meta.deform import (
    extract_static_address,
    reconstruct_with_flat_ref,
    walk_ref_chain,
)


__all__ = [
    "extract_static_address",
    "reconstruct_with_flat_ref",
    "walk_ref_chain",
]
