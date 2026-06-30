"""Shapes tree utilities - ref chain deformation, annotation, flow-aware wrapping."""

from .annotate import annotate_ref_loads
from .deform import extract_static_address, reconstruct_with_flat_ref, walk_ref_chain
from .wrap import has_write_on_fabric, is_flow, touches_fabric, wrap_flow_children, wrap_flows


__all__ = [
    "annotate_ref_loads",
    "extract_static_address",
    "has_write_on_fabric",
    "is_flow",
    "reconstruct_with_flat_ref",
    "touches_fabric",
    "walk_ref_chain",
    "wrap_flow_children",
    "wrap_flows",
]
