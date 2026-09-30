"""The kv leaf for a path: kept as its str in KV storage.

The leaf pairs the ``nustd.pathlib`` value form with the kv leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaf lives with
its library, not in ``nustd.kv``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import ToStr
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nustd.kv.refs import ItemRef
from nustd.pathlib.forms import Path as PathForm


if TYPE_CHECKING:
    from pathlib import PurePath

    from nu.lang import Arg


__all__ = ["PathRef"]


class PathRef(ItemRef, PathForm):
    """A filesystem path leaf in KV storage, stored as its str form.

    Notes:
        - Reads come back as a PurePath, so the path surface is the pure
          one: parts, parents, suffixes, joins. Nothing here touches a
          filesystem.
        - Stored as written, so a path written on one platform reads back
          with that platform's separators.
        - An absent leaf reads as EMPTY.

    Example:
        class Job(Shape):
            outdir = PathRef.slot()
        run(Job.outdir.set(PurePath("/var/log")), ctx)
    """

    def _lift(self, raw: object) -> PurePath:
        """Parse the stored str back to a PurePath."""
        from pathlib import PurePath

        return raw if isinstance(raw, PurePath) else PurePath(str(raw))

    def set(self, value: Arg[PurePath | str]) -> SetCmd:
        """Write a path to the leaf, serialized to str.

        Args:
            value: a path, a str, or an expression yielding either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr.

        Example:
            run(Job.outdir.set(PurePath("/var/log")), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
