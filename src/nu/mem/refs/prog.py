"""Dict-substrate ref for a stored Nu program.

``ProgramRef`` is a slot in the nested-dict substrate whose stored value is
python source text and whose value interface is
:class:`~nu.prog.forms.Program`. That makes a program a first-class slot on
a Shape::

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

    from .base import RefBase


__all__ = ["ProgramRef"]


class ProgramRef(ItemRef, Program):
    """A slot holding Nu program source, with the Program verbs on it.

    The stored value is Python source text defining ``out()``, and the same
    text on both sides: no codec, unlike the ``std`` refs whose domain type
    the substrate cannot hold. What the ``Program`` mixin adds is the
    interface - ``load`` constructs the tree the source describes, ``run``
    constructs it and evaluates it - so a program becomes a field like any
    other, written and rewritten while the app is up.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Base order is load-bearing. ``ItemRef`` reaches ``RefBase``, which
          declares ``Sort.REF`` and compiles to a fabric read; ``Program``
          reaches ``TypedNu``, which declares a scalar query and compiles to
          a passthrough over child 0. Flipped, ``TypedNu`` wins both: the ref
          yields its parent ref instead of the stored value and the effect
          machinery stops seeing a fabric touch, silently.
        - Reading the ref yields the source verbatim; the ``Program`` calls
          are what turn it into a tree.
        - ``run`` on a slot that was never written raises rather than
          yielding a sentinel: construction gets EMPTY where it wants source.

    Yields:
        The stored source text. EMPTY when the slot was never written.

    Example:
        >>> class App(nu.Shape):
        ...     job = nu.mem.ProgramRef.slot()
        >>> source = '''
        ... import nu
        ...
        ... def out():
        ...     return nu.Add(1, 2)
        ... '''
        >>> ctx = nu.Context().bind(dict, {}, App)
        >>> _ = nu.run(App.job.set(source), ctx)
        >>> nu.run(App.job.run(), ctx)[0]
        3
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a slot holding Nu program source text.

        Example:
            class App(Shape):
                job = ProgramRef.slot()
        """
        return Slot(cls)  # type: ignore[return-value]
