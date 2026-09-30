"""The kv leaf for a UUID: kept as its hyphenated str in KV storage.

The leaf pairs the ``nustd.uuid`` value form with the kv leaf and
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
from nustd.uuid.forms import UUID as UUIDForm


if TYPE_CHECKING:
    from uuid import UUID

    from nu.lang import Arg


__all__ = ["UUIDRef"]


class UUIDRef(ItemRef, UUIDForm):
    """A UUID leaf in KV storage, stored as its canonical hyphenated str.

    Notes:
        - Str on disk rather than 16 raw bytes, so the stored value is
          readable in a dump and matches what other systems expect.
        - Reads parse back to a UUID, so ``version``, ``int_`` and ``hex``
          are on the ref.
        - An absent leaf reads as EMPTY.

    Example:
        class Session(Shape):
            token = UUIDRef.slot()
        run(Session.token.set(uuid4()), ctx)
    """

    def _lift(self, raw: object) -> UUID:
        """Parse the stored str back to a UUID."""
        import uuid

        return raw if isinstance(raw, uuid.UUID) else uuid.UUID(str(raw))

    def set(self, value: Arg[UUID | str]) -> SetCmd:
        """Write a UUID to the leaf, serialized to str.

        Args:
            value: a UUID, a str spelling one, or an expression yielding
                either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr.
            - Any spelling ``UUID()`` accepts reads back, so a str without
              hyphens still parses; it is stored as given.

        Example:
            run(Session.token.set(uuid4()), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
