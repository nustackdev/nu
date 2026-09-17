"""Boot chains: what a Shape's slots look like as init frames.

A chain is one root-first walk of ``(segment, type, props)`` per level -- the
same shape a write carries, minus the payload. Shipped at boot as ``init``
frames so a slot is on screen before anything writes to it, and dropped into
the browser's tree by the same autovivify walk a write takes.

Host-independent on purpose. The two hosts that boot a shape tree do the
identical walk over their own top-level kind (nudle's Index / Page, nuspace's
Shell / Screen), and nothing in the walk knows which one it is looking at: a
Section slot contributes its own level and then everything under it, which is
how a nested surface lands one segment below its container.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import Ref, _wire_type_of
from .section import SectionRef


if TYPE_CHECKING:
    from nu.domains.shape import Shape

    from .section import Section


__all__ = ["Chain", "boot_chains"]


#: One chain, root-first: ``(segment, type, props)`` per level. What a write
#: carries and what a boot ``init`` frame is made of.
Chain = tuple[tuple[str, str, dict[str, Any]], ...]


def boot_chains(base: Chain, shape_cls: type[Shape]) -> list[Chain]:
    """Every slot under ``shape_cls`` as a chain, root-first, in order.

    Depth-first in declaration order, so the browser's per-node insertion
    order is the order the class body reads. A Section slot contributes its
    own level and then everything under it.
    """
    out: list[Chain] = []
    for name, slot in shape_cls._slots.items():
        ref_cls = slot.ref_cls
        if not issubclass(ref_cls, Ref):
            continue
        if issubclass(ref_cls, SectionRef):
            section_cls: type[Section] = slot.kwargs["section_cls"]
            chain = (*base, (name, _wire_type_of(section_cls), dict(slot.props)))
            out.append(chain)
            out.extend(boot_chains(chain, section_cls))
            continue
        out.append((*base, (name, _wire_type_of(ref_cls), dict(slot.props))))
    return out
