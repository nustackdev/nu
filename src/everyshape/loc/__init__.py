"""Location System.

Each layer has its own location abstraction:

    key → site → path → ref

- Key (Storage): raw tuple coordinates
- Site (Container): hierarchical place
- Path (View): typed navigation segments
- Ref (Shape): declarative handle

See docs/philosophy/location_vocab.md for details.
"""

from . import key, path, site


__all__ = [
    "key",
    "path",
    "site",
]
