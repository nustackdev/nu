"""Named child keys: the children a container draws in a place of its own, not the body.

A Card draws ``media`` on top, ``actions`` on its header's right rail and
``footer`` along the bottom; a PageSection draws ``actions`` on its header's
right. Each is a key like any child's, so a Shape declares it as a slot of
that name and a program builds it with ``parent_ref=``. The properties on
the Refs (``card.actions``, ``section.actions``) answer with the Shape's slot
when it declares one, and with a default container there when it does not.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .flow import ColumnRef, RowRef


if TYPE_CHECKING:
    from nustd.ui.core import Ref


__all__ = ["ACTIONS", "FOOTER", "MEDIA", "actions_ref", "footer_ref", "media_ref"]


#: The child key a Card or a PageSection draws on its header's right.
ACTIONS = "actions"

#: The child key a Card draws full-bleed on top, above its header.
MEDIA = "media"

#: The child key a Card draws along its bottom edge, pinned there.
FOOTER = "footer"

# A row of small controls: buttons, badges, icon buttons, centred on the line.
_ROW_PROPS = {"gap": 2, "align": "center"}


def _named_ref(ref: Ref, key: str, default: type[Ref], props: dict[str, object]) -> Ref:
    """The Shape's slot at ``key`` under ``ref``, or a ``default`` container there."""
    section_cls = ref._payload.get("section_cls")
    slots = getattr(section_cls, "_slots", {})
    if key in slots:
        return slots[key].create_ref(owner_shape=section_cls, parent_ref=ref)
    return default(key, parent_ref=ref, props=props)


def actions_ref(ref: Ref, **row_props: object) -> Ref:
    """The header actions under ``ref``: its Shape's ``actions`` slot, or a Row there."""
    return _named_ref(ref, ACTIONS, RowRef, {**_ROW_PROPS, **row_props})


def footer_ref(ref: Ref, **row_props: object) -> Ref:
    """The footer under ``ref``: its Shape's ``footer`` slot, or a Row there."""
    return _named_ref(ref, FOOTER, RowRef, {**_ROW_PROPS, **row_props})


def media_ref(ref: Ref, **column_props: object) -> Ref:
    """The media under ``ref``: its Shape's ``media`` slot, or a gapless Column there."""
    return _named_ref(ref, MEDIA, ColumnRef, {"gap": 0, **column_props})
