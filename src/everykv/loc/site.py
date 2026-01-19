"""Site location for Container layer.

A Site is a hierarchical location in the container tree.
It's the same tuple type as Key, but with structural semantics:

    - Key (Storage): raw coordinates, flat join operations
    - Site (Container): hierarchical place with parent-child relationships

Sites are used in the container layer to represent locations
where containers and primitives live.

Example:
    >>> from everyshape.loc import site
    >>> s = ("users", "alice", "profile")
    >>> site.get_parent(s)
    ("users", "alice")
    >>> site.get_ancestors(s)
    [("users",), ("users", "alice")]
    >>> site.is_ancestor(("users",), s)
    True
"""

from __future__ import annotations

from .site_def import *  # noqa: F403
from .site_nav import *  # noqa: F403
