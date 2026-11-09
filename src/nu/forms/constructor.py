"""Value constructors: the classmethods that build a fresh value, absent on refs.

``Dict.of``, ``List.create`` and their siblings build a value. A ref class names
a place in a fabric, not a value, so it inherits the form's surface but not its
constructors: they are declared with ``value_constructor``, which a ``Ref``
subclass does not have.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Ref


__all__ = [
    "value_constructor",
]


if TYPE_CHECKING:
    # to a type checker it is a plain classmethod; only the runtime lookup differs
    from builtins import classmethod as value_constructor
    from collections.abc import Callable
else:

    class value_constructor(classmethod):  # noqa: N801  # a decorator, named like classmethod
        """A classmethod that builds a value, so a ref class has none.

        Notes:
            - Reading it off a ``Ref`` subclass, or a ref, raises
              ``AttributeError``: ``hasattr(DictRef, "of")`` is False.
        """

        def __get__(self, obj: object, owner: type | None = None) -> Callable[..., object]:
            owner = type(obj) if owner is None else owner
            if issubclass(owner, Ref):
                name = self.__func__.__name__
                msg = (
                    f"{owner.__name__}.{name}: a ref names a place and builds no value, "
                    f"use {self.__func__.__qualname__} for one"
                )
                raise AttributeError(msg)
            return super().__get__(obj, owner)
