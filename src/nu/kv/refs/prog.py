"""Virtuals-substrate ref for a stored Nu program.

``ProgramRef`` is a leaf whose stored value is python source text and whose
value interface is :class:`~nu.prog.forms.Program`. That makes a program a
first-class slot on a Shape::

    class App(Shape):
        job = ProgramRef.slot()

    run(App.job.set(SOURCE), ctx)
    run(App.job.run(), ctx)

No codec, unlike its neighbours in ``std``. ``DecimalRef`` and friends
override ``_lift`` / ``set`` because their domain type is not what the
substrate can hold; a program is source text on both sides, so the stored
form *is* the domain form and there is nothing to translate. The mixin is
carrying an interface, not a representation.

MRO note: ``ItemRef`` comes first, ``Program`` second. That order decides
whose ``_compile`` and whose declared ``sort`` win, and getting it backwards
is silent - see the class docstring.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nu.domains.shape import Slot
from nu.prog import Program

from .items import ItemRef


if TYPE_CHECKING:
    from nu.domains.shape import Shape
    from nu.lang import IntArg, StrArg

    from .base import PrimitiveRef


__all__ = ["ProgramRef"]


class ProgramRef(ItemRef, Program):
    """Virtuals reference to stored program source, with the Program verbs.

    Bases are ordered substrate-first for a reason. ``ItemRef`` reaches the
    virtuals ``PrimitiveRef``, which declares ``sort = Sort.REF`` and
    compiles to a fabric read; ``Program`` reaches ``TypedNu``, which
    declares a scalar query and compiles to a passthrough over child 0.
    Flipped, ``TypedNu`` would win both: the ref would yield its *parent*
    ref instead of the stored value, and the effect machinery would stop
    seeing a fabric touch. Nothing raises. This order is load-bearing.
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Program,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding Nu program source."""
        return Slot(cls)  # type: ignore[return-value]
