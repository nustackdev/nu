"""Serializable path types for proxy-transparent navigation.

Concrete tuple subclasses that can be registered with invisibles as
value types, so the entire path (including class references) is pickled
by value rather than proxied element-by-element.

Register with invisibles at process startup::

    from invisibles.core.boxing import register_value_type
    from nu_virtuals.paths import ViewPathSer, ValuePathSer

    register_value_type(ViewPathSer, ValuePathSer)
"""

from __future__ import annotations


__all__ = [
    "ValuePathSer",
    "ViewPathSer",
]


class ViewPathSer(tuple):
    """Serializable path to a view. Tuple of (address, view_type) segments."""


class ValuePathSer(tuple):
    """Serializable path to a value. View segments + final (address, value_type)."""
