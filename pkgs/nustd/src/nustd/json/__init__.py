"""Nu surface for Python's ``json`` module.

``json`` is a function module, so the Nu surface mirrors that: ``loads`` and
``dumps`` as free functions, plus ``JSONDecodeError`` re-exported so callers
catch the same class they would with the stdlib. Two layers behind it:
``functions`` (the wrappers) and ``interactions`` (the atoms each wrapper
builds). Import it the way you would the stdlib::

    import nustd.json as json

    meta = json.loads(fs_ref.read_text("meta.json"))
    fs_ref.write_text("meta.json", json.dumps(meta, indent=2))

``load`` / ``dump`` are left out on purpose: they take file objects, and a file
object is not a value a Nu tree carries. Read the text through a fabric (an fs
read gives a ``str``) and hand it to ``loads``; build the text with ``dumps``
and write it back the same way.
"""

from __future__ import annotations

from json import JSONDecodeError

from nustd.json.functions import dumps, loads


__all__ = [
    "JSONDecodeError",
    "dumps",
    "loads",
]
