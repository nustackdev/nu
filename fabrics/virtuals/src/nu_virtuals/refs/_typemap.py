"""Shared utility: map a Python type to its primitive Form class.

Used by the collection refs to pick the value/key Form for a slot's declared
element type (e.g. ``ListRef.slot(str)`` -> ``StrForm``). Single source of truth
so the mapping is not repeated per ref module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import (
    AnyForm,
    BoolForm,
    BytesForm,
    DictForm,
    FloatForm,
    IntForm,
    ListForm,
    SetForm,
    StrForm,
)


if TYPE_CHECKING:
    from nu import Form


__all__ = ["value_type_for"]


_FORM_BY_TYPE: dict[type, type] = {
    int: IntForm,
    str: StrForm,
    float: FloatForm,
    bool: BoolForm,
    bytes: BytesForm,
    list: ListForm,
    dict: DictForm,
    set: SetForm,
}


def value_type_for(python_type: type) -> type[Form]:
    """Map a Python type to its corresponding primitive Form (``AnyForm`` fallback)."""
    return _FORM_BY_TYPE.get(python_type, AnyForm)
