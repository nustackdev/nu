"""The mem leaf for a UUID: kept as its hyphenated str in a plain dict.

The leaf pairs the ``nustd.uuid`` value form with the mem leaf and
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
from nustd.uuid.forms import UUID as UUIDForm


if TYPE_CHECKING:
    from uuid import UUID

    from nu.lang import Arg


__all__ = ["UUIDRef"]


class UUIDRef(ItemRef, UUIDForm):
    """A UUID slot in the dict substrate, stored as its hyphenated string.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Parsing on read is ``uuid.UUID(str)``, which takes the hyphenated
          form, a bare hex run, or a URN, so a hand-filled dict is forgiving.

    Yields:
        A UUID parsed from the stored string. EMPTY when the slot was never
        written.

    Example:
        >>> import uuid
        >>> class Row(nu.Shape):
        ...     rid = nustd.uuid.mem.UUIDRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Row)
        >>> _ = nu.run(Row.rid.set(uuid.UUID(int=1)), ctx)
        >>> data
        {'rid': '00000000-0000-0000-0000-000000000001'}
        >>> nu.run(Row.rid.int_(), ctx)[0]
        1
    """

    def _lift(self, raw: object) -> UUID:
        """Parse the stored str back to a UUID."""
        import uuid

        return raw if isinstance(raw, uuid.UUID) else uuid.UUID(str(raw))

    def set(self, value: Arg[UUID | str]) -> SetCmd:
        """Write a UUID into the slot as its hyphenated string.

        Notes:
            - A plain Python value goes through ``str`` at tree-build time; a
              Nu operand gets a ``ToStr`` node.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
