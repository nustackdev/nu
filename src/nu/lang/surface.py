"""Surface: the methods side of a form.

A form is two things that used to be one class. The node is ``Form``
(``nu.lang.form``): a Span that wraps one body and forwards its yield. The
methods are a ``Surface``: a plain mixin with no sort, no cardinality and no
compile, so a value form and a Ref can share one method set without either
inheriting the other's kind::

    Str(StrSurface, Form)               value form: the Span node
    StrRef(MutableItemRef, StrSurface)  Ref: the Ref node, same methods

``Surface`` is the root of every family's surface. It carries what all of them
share: the NULL helpers, ``==`` / ``!=`` and ``fallback``, plus the
``type_info`` field (the declared key and element types a typed collection
keeps, so its own ops stay typed). Static typing rides the ``Nu[T]`` generics
of the node a surface is mixed into; a surface carries no type parameter of
its own.

The NULL-check helpers and ``Bool`` they return live in ``nu.forms``;
``Surface`` reaches them with a lazy import so this module keeps no
import-time dependency on the forms package (it would be a cycle: forms
imports ``Surface``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from .form import Form
from .kinds import Ref
from .nu import Nu


if TYPE_CHECKING:
    from typing_extensions import Self

    from nu.forms import Bool
    from nu.lang.typeinfo import TypeInfo


__all__ = ["Surface"]


class Surface(Nu):
    """The methods mixin every form and every typed Ref shares.

    Contributes the NULL helpers, ``fallback`` and ``==`` / ``!=``: on a
    Surface they build ``Eq`` / ``Ne`` over the values it yields (the bare
    ``Nu`` base raises instead). A family narrows the operand type by
    overriding them; a family with no value equality raises.

    No kind: it declares no sort, cardinality or compile, so it is never a
    node on its own. Mix it into one (a ``Form``, a Ref). It subclasses
    the bare ``Nu`` base so Python's MRO always puts it ahead of ``Nu``: its
    dunders win over the ones every term carries whichever order the node
    lists its bases in. It has no ``__init__``: the node it is mixed into
    builds the term and sets ``_type_info`` (a value form from its
    ``type_info`` keyword, a Ref from its slot), so the surface never sits in
    a constructor chain.
    """

    _type_info: TypeInfo | None = None
    """The declared types this value carries (a typed collection's key and
    element), so its own ops stay typed. None when nothing is declared."""

    _value_form_cls: ClassVar[type[Form] | None] = None
    """The value form this surface reads as, set when a Form first mixes it
    in directly (``Str(StrSurface, Form)`` sets ``StrSurface``'s to ``Str``).
    Lets a Ref, which has the surface but no Form, read as its value form."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not issubclass(cls, Form) or issubclass(cls, Ref):
            return
        for base in cls.__bases__:
            if (
                issubclass(base, Surface)
                and not issubclass(base, Form)
                and "_value_form_cls" not in base.__dict__
            ):
                base._value_form_cls = cls

    def __eq__(self, other: object) -> Bool:  # type: ignore[override]
        """Self equal to other by value: an ``Eq`` term, never a Python bool."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: object) -> Bool:  # type: ignore[override]
        """Self not equal to other by value: a ``Ne`` term, never a Python bool."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))

    def is_null(self) -> Bool:
        """True if this value is NULL. On a container ref ask ``exists()`` instead."""
        from nu.core import IsNull
        from nu.forms import Bool

        return Bool(IsNull(self))

    def fallback(self, *alternatives: object) -> Self:
        """The first of this value and ``alternatives`` that is not NULL.

        Args:
            *alternatives: the values to try in order when this one is NULL.
                At least one.

        Notes:
            - Checks NULL, not truthiness: ``0``, ``""``, ``False`` and
              ``None`` are values and are kept.
            - Evaluates only as far as it needs: an alternative after the
              first non-NULL value never runs.
            - Reads as this value's Form, so the result keeps its surface
              (a ``Str`` stays a ``Str``, a ``StrRef`` reads as ``Str``).

        Yields:
            The first non-NULL value. NULL only when all of them are NULL.

        Example:
            >>> class User(nu.Shape):
            ...     name = nu.StrRef.slot()
            >>> ctx = nu.Context().bind(dict, {}, User)
            >>> nu.run(User.name.fallback("guest").upper(), ctx)[0]
            'GUEST'
            >>> nu.run(nu.Int(0).fallback(5))[0]
            0
        """
        from nu.core import Fallback

        if not alternatives:
            msg = "fallback() needs at least one alternative"
            raise TypeError(msg)
        return self._value_form()(Fallback(self, *alternatives))  # type: ignore[call-arg, return-value]

    def _value_form(self) -> type[Form]:
        """This surface's value Form: the node itself, or what a Ref's surface reads as.

        A value form answers its own class (the first Form in the MRO that is
        no Ref). A Ref has no Form, so it answers the value form its nearest
        surface was registered with: a ``StrRef`` reads as ``Str``. ``Object``
        when neither is found.
        """
        for cls in type(self).__mro__:
            if issubclass(cls, Form) and not issubclass(cls, Ref):
                return cls
            registered = cls.__dict__.get("_value_form_cls")
            if registered is not None:
                return registered  # type: ignore[no-any-return]
        from nu.forms import Object

        return Object
