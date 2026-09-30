"""The mem leaf for a path: kept as its str in a plain dict.

The leaf pairs the ``nustd.pathlib`` value form with the mem leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaf lives with
its library, not in ``nu.mem``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import ToStr
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nu.mem.refs import ItemRef
from nustd.pathlib.forms import Path as PathForm


if TYPE_CHECKING:
    from pathlib import PurePath

    from nu.lang import Arg


__all__ = ["PathRef"]


class PathRef(ItemRef, PathForm):
    """A filesystem path slot in the dict substrate, stored as a plain str.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Lifted to a ``PurePath``, so the flavour follows the machine
          reading it: the same stored string is a PurePosixPath on Linux and
          a PureWindowsPath on Windows.
        - Pure means no filesystem: the calls take the path apart and put it
          back together, they never touch disk.

    Yields:
        A PurePath built from the stored string. EMPTY when the slot was
        never written.

    Example:
        >>> from pathlib import PurePath
        >>> class Cfg(nu.Shape):
        ...     root = nustd.pathlib.mem.PathRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Cfg)
        >>> _ = nu.run(Cfg.root.set(PurePath("/srv/app.toml")), ctx)
        >>> data
        {'root': '/srv/app.toml'}
        >>> nu.run(Cfg.root.name(), ctx)[0]
        'app.toml'
    """

    def _lift(self, raw: object) -> PurePath:
        """Parse the stored str back to a PurePath."""
        from pathlib import PurePath

        return raw if isinstance(raw, PurePath) else PurePath(str(raw))

    def set(self, value: Arg[PurePath | str]) -> SetCmd:
        """Write a path into the slot as a plain string.

        Notes:
            - A plain Python value goes through ``str`` at tree-build time; a
              Nu operand gets a ``ToStr`` node.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
