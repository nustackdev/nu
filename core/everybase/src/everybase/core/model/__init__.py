"""Model system -- abstract bases for declarative structure definitions.

Model:
    Abstract base for all data models. Substrate packages extend this:
    - everyshape.Shape: document model (hierarchical key-value)
    - everytable.Table: relational model (future)
"""

from __future__ import annotations

from .model import Model


__all__ = [
    "Model",
]
