"""A container slot refuses a container ref as its value: use a Shape.

``DictRef.slot(OrderedDictRef[str, bool])`` used to build, and every value
then landed as one opaque blob, with no keys, order or watch of its own. Each
container slot now raises where it is declared, in the ``slot()`` form and the
annotation form alike. Leaves, blob refs and Shapes stay fine as values.
"""

from __future__ import annotations

import pytest

from nu import Shape
from nustd.kv import (
    DictRef,
    IntRef,
    Kh57Ref,
    ListRef,
    OrderedDictRef,
    PrimitiveListRef,
    SetRef,
    ShapeRef,
)


class Ids(Shape):
    ids = OrderedDictRef.slot(bool)


DECLARATIONS = {
    "dict_of_ordered": lambda: DictRef.slot(OrderedDictRef[str, bool]),
    "dict_of_set": lambda: DictRef.slot(SetRef[str]),
    "dict_of_bare_dict": lambda: DictRef.slot(DictRef),
    "dict_of_shape_ref": lambda: DictRef.slot(ShapeRef),
    "ordered_of_list": lambda: OrderedDictRef.slot(ListRef[int]),
    "kh57_of_dict": lambda: Kh57Ref.slot(DictRef[str, int]),
    "list_of_dict": lambda: ListRef.slot(DictRef[str, int]),
    "set_of_list": lambda: SetRef.slot(ListRef[int]),
}


@pytest.mark.parametrize("name", DECLARATIONS)
def test_a_container_ref_value_is_refused(name) -> None:
    with pytest.raises(TypeError, match="Use a Shape"):
        DECLARATIONS[name]()


def test_the_message_names_the_slot_and_the_value() -> None:
    with pytest.raises(TypeError, match=r"DictRef\.slot\(OrderedDictRef\)"):
        DictRef.slot(OrderedDictRef[str, bool])


def test_the_annotation_form_is_refused_at_class_build() -> None:
    with pytest.raises(TypeError, match="Use a Shape"):

        class Bad(Shape):
            planes: DictRef[str, OrderedDictRef[str, bool]]


def test_the_wrapper_shape_is_the_way() -> None:
    class Space(Shape):
        spec_planes = DictRef.slot(Ids)
        counts: DictRef[str, int]
        blobs = DictRef.slot(PrimitiveListRef)
        leaves = Kh57Ref.slot(IntRef)

    assert type(Space.spec_planes["s"].ids).__name__ == "OrderedDictRef"
    assert type(Space.blobs["b"]).__name__ == "PrimitiveListRef"
