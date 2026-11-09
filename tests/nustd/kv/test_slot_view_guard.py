"""A container slot refuses a view that cannot serve its ref's surface.

Every call on a kv ref runs on its view, and a ref carries its grid cell's
whole surface: a ``DictRef`` reverses, merges and watches, a ``ShapeRef``
watches. So ``slot(view=)`` checks the view class has the bases behind that
surface and raises a clear TypeError where the slot is declared, the way
``RingRef.slot`` checks for a ring.
"""

from __future__ import annotations

import pytest

from nu import Shape
from nustd.kv import (
    DictRef,
    Kh57Ref,
    ListRef,
    LogDictRef,
    OrderedDictRef,
    SetRef,
    ShapeRef,
)
from virtuals.views import (
    DictView,
    EagerFractionalIndexedDictView,
    EagerIndexedDictView,
    EagerLogIndexedDictView,
    FlatDictView,
    FlatListView,
    FrozenSetView,
    Kh57View,
    LazyDictView,
    LazyLogIndexedDictView,
    LightDictView,
    ListView,
    RingView,
    SetView,
    TupleView,
)


class Field(Shape):
    pass


FITS = {
    "dict_on_dict": lambda: DictRef.slot(int, view=DictView),
    "dict_on_lazy_dict": lambda: DictRef.slot(int, view=LazyDictView),
    "dict_on_flat": lambda: DictRef.slot(int, view=FlatDictView),
    "dict_on_light": lambda: DictRef.slot(int, view=LightDictView),
    "dict_on_indexed": lambda: DictRef.slot(int, view=EagerIndexedDictView),
    "dict_on_log": lambda: DictRef.slot(int, view=LazyLogIndexedDictView),
    "list_on_list": lambda: ListRef.slot(int, view=ListView),
    "list_on_flat": lambda: ListRef.slot(int, view=FlatListView),
    "set_on_set": lambda: SetRef.slot(int, view=SetView),
    "shape_on_dict": lambda: ShapeRef.slot(Field, view=DictView),
    "shape_on_kh57": lambda: ShapeRef.slot(Field, view=Kh57View),
    "ordered_on_fractional": lambda: OrderedDictRef.slot(bool, view=EagerFractionalIndexedDictView),
    "log_on_log": lambda: LogDictRef.slot(bool, view=EagerLogIndexedDictView),
    "kh57_on_kh57": lambda: Kh57Ref.slot(int, view=Kh57View),
}

REFUSED = {
    "dict_on_kh57": lambda: DictRef.slot(int, view=Kh57View),
    "dict_on_list": lambda: DictRef.slot(int, view=ListView),
    "dict_on_not_a_class": lambda: DictRef.slot(int, view="DictView"),  # type: ignore[arg-type]
    "list_on_tuple": lambda: ListRef.slot(int, view=TupleView),  # type: ignore[arg-type]
    "list_on_ring": lambda: ListRef.slot(int, view=RingView.of(3)),  # type: ignore[arg-type]
    "set_on_frozenset": lambda: SetRef.slot(int, view=FrozenSetView),  # type: ignore[arg-type]
    "shape_on_list": lambda: ShapeRef.slot(Field, view=ListView),  # type: ignore[arg-type]
    "ordered_on_dict": lambda: OrderedDictRef.slot(bool, view=DictView),  # type: ignore[arg-type]
    "log_on_dict": lambda: LogDictRef.slot(bool, view=DictView),  # type: ignore[arg-type]
    "kh57_on_dict": lambda: Kh57Ref.slot(int, view=DictView),  # type: ignore[arg-type]
}


@pytest.mark.parametrize("declare", FITS.values(), ids=FITS.keys())
def test_a_view_that_fits_the_ref_declares(declare):
    declare()


@pytest.mark.parametrize("declare", REFUSED.values(), ids=REFUSED.keys())
def test_a_view_that_does_not_fit_raises_at_declaration(declare):
    with pytest.raises(TypeError, match=r"\.slot\(view=.*the view must be"):
        declare()


def test_the_error_names_the_ref_the_view_and_what_fits():
    with pytest.raises(TypeError) as err:
        DictRef.slot(int, view=Kh57View)
    msg = str(err.value)
    assert msg.startswith("DictRef.slot(view=")
    assert "Kh57View" in msg
    assert "reactive dict view" in msg
