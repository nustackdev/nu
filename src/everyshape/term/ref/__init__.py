"""Typed reference to storage location.

Term                        - executable node
├── LValue                  - addressable location (has path)
│   └── Ref                 - typed reference to storage location
│       ├── ViewRef         - reference to container (dict, list, set)
│       └── PrimitiveRef    - reference to leaf value (int, str, etc.)
"""

from __future__ import annotations

from .ref import PrimitiveRef, Ref, ViewRef


__all__ = [
    "PrimitiveRef",
    "Ref",
    "ViewRef",
]
