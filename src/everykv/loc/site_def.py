"""Site location for Container layer.

A Site is a hierarchical location in the container tree.
It's the same tuple type as Key, but with structural semantics:

    - Key (Storage): raw coordinates, flat join operations
    - Site (Container): hierarchical place with parent-child relationships

Sites are used in the container layer to represent locations where containers and primitives live.

"""

from __future__ import annotations

from .key_def import Key, KeySegment


__all__ = [
    "Site",
    "SiteSegment",
]

# Site is the same tuple type as Key, but with hierarchical semantics
type Site = Key
type SiteSegment = KeySegment
