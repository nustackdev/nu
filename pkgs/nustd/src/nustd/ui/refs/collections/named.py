"""Named child keys: the children a container draws in a place of its own, not the body.

A Card draws ``media`` on top, ``actions`` on its header's right rail and
``footer`` along the bottom; a PageSection draws ``actions`` on its header's
right. Each is a key like any child's, so a Shape declares it as a slot of
that name and a program builds it with ``parent_ref=``. The properties on
the Refs (``card.actions``, ``section.actions``, ``field.control``) answer
with the Shape's slot when it declares one, and with the part's default kind
there when it does not (a bare child for a Field's control). ``ref["actions"]``
is refused: the part is reached by its property, so one place never holds
two kinds.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nustd.ui.core import child_at

from .flow import ColumnRef, RowRef


if TYPE_CHECKING:
    from nu.domains.shape import Slot
    from nustd.ui.core import Ref


__all__ = [
    "ACTIONS",
    "CONTROL",
    "FOOTER",
    "MEDIA",
    "actions_ref",
    "footer_ref",
    "media_ref",
    "part_ref",
]


#: The child key a Card or a PageSection draws on its header's right.
ACTIONS = "actions"

#: The child key a Card draws full-bleed on top, above its header.
MEDIA = "media"

#: The child key a Card draws along its bottom edge, pinned there.
FOOTER = "footer"

#: The child key a Field draws its one control at, when no Shape names it.
CONTROL = "control"

# A row of small controls: buttons, badges, icon buttons, centred on the line.
_ROW_PROPS = {"gap": 2}


def part_ref(ref: Ref, key: str, default: Slot | None) -> Ref:
    """The part ``key`` under ``ref``: its Shape's slot of that name, else ``default`` there.

    ``default`` is a spec (``RowRef.slot(gap=2)``), or None for a bare child
    whose kind ``.to`` names. Either way ``.to`` re-kinds the part in place.
    """
    section_cls = ref._payload.get("section_cls")
    slots = getattr(section_cls, "_slots", {})
    if key in slots:
        return slots[key].create_ref(owner_shape=section_cls, parent_ref=ref)
    return child_at(ref, key, default)


def actions_ref(ref: Ref, **row_props: object) -> Ref:
    """The header actions under ``ref``: its Shape's ``actions`` slot, or a Row there."""
    return part_ref(ref, ACTIONS, RowRef.slot(**{**_ROW_PROPS, **row_props}))


def footer_ref(ref: Ref, **row_props: object) -> Ref:
    """The footer under ``ref``: its Shape's ``footer`` slot, or a Row there."""
    return part_ref(ref, FOOTER, RowRef.slot(**{**_ROW_PROPS, **row_props}))


def media_ref(ref: Ref, **column_props: object) -> Ref:
    """The media under ``ref``: its Shape's ``media`` slot, or a gapless Column there."""
    return part_ref(ref, MEDIA, ColumnRef.slot(**{"gap": 0, **column_props}))
