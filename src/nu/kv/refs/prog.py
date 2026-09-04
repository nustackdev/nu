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
    """A Nu program stored as source text in a KV leaf, with the Program verbs.

    Reading it yields the source verbatim, the same as any str leaf. What the
    Program surface adds is the ability to turn that stored text into a tree
    and run it, so a program becomes a value a shape can hold, write and
    replace at run time.

    Notes:
        - No codec: source text is both the stored form and the value form,
          unlike the std refs that translate between the two.
        - The base order is load-bearing. ``ItemRef`` first makes the class a
          ref that reads storage; with ``Program`` first the passthrough
          would win and the ref would yield its parent instead of the stored
          value, silently, with no fabric touch recorded.
        - Construction errors surface when the stored source is loaded or
          run, not when it is written, so bad source stores fine.

    Example:
        class App(Shape):
            job = ProgramRef.slot()
        run(App.job.set(SOURCE), ctx)
        run(App.job.run(), ctx)
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
