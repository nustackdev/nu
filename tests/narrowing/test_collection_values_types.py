"""Typing tests: decomposed collections typed by the value they declare.

``DictRef[K, str]`` subscripts to a ``StrRef``, ``ListRef[int]`` to an
``IntRef``, a kv leaf class to itself, and an undeclared (``object``) value to
``ObjectRef``. ``.iter()`` streams the declared element type (a mapping's key
type). The ``.slot(...)`` spelling types the same as the annotation, in both
fabrics.
"""

from __future__ import annotations

from typing_extensions import assert_type

import nu
import nustd
from nu.forms import Bool, Int, Iterator, List, Object, Set, Str
from nustd.kv.refs import (
    BoolRef,
    DecimalRef,
    DictRef,
    FloatRef,
    IntRef,
    Kh57Ref,
    ListRef,
    ObjectRef,
    StrRef,
)


class Store(nu.Shape):
    names: DictRef[str, str]
    counts: DictRef[str, int]
    flags: DictRef[int, bool]
    prices: DictRef[str, DecimalRef]
    meta: DictRef[str, object]
    tags: ListRef[str]
    blobs: ListRef[object]
    series: Kh57Ref[float]


# --- Subscript -> the value's leaf ------------------------------------


assert_type(Store.names["a"], StrRef)
assert_type(Store.counts["a"], IntRef)
assert_type(Store.flags[1], BoolRef)
assert_type(Store.prices["a"], DecimalRef)
assert_type(Store.tags[0], StrRef)
assert_type(Store.series[7], FloatRef)


# --- Undeclared value -> ObjectRef -------------------------------------


assert_type(Store.meta["a"], ObjectRef)
assert_type(Store.blobs[0], ObjectRef)


# --- The leaf is an operand of its value ------------------------------


assert_type(Store.names["a"].upper(), Str)
assert_type(Store.counts["a"] + 1, Int)
assert_type(Store.tags[0] + "!", Str)
assert_type(Store.counts["a"] > Store.counts["b"], Bool)


# --- A slice stays a value ---------------------------------------------


assert_type(Store.tags[0:2], List[str])


# --- A stream carries the declared element type ------------------------


assert_type(Store.tags.iter(), Iterator[str])
assert_type(Store.tags.iter().first(), Str)
assert_type(Store.counts.iter().first(), Str)
assert_type(Store.flags.iter().first(), Int)
assert_type(Store.tags.iter().filter(nu.Attr("item")).first(), Str)
assert_type(Store.tags.iter().to_list(), List[str])
assert_type(Store.tags.iter().to_set(), Set[str])
assert_type(Store.blobs.iter().first(), Object)


# --- The slot spelling types the same ----------------------------------


class Spelled(nu.Shape):
    names = nustd.kv.DictRef.slot(str)
    by_id = nustd.kv.DictRef.slot(int, key=int)
    tags = nustd.kv.ListRef.slot(str)
    meta = nustd.kv.DictRef.slot(object)
    mem_names = nustd.mem.DictRef.slot(str)
    mem_tags = nustd.mem.ListRef.slot(int)


assert_type(Spelled.names, DictRef[str, str])
assert_type(Spelled.by_id, DictRef[int, int])
assert_type(Spelled.names["a"], StrRef)
assert_type(Spelled.by_id[1], IntRef)
assert_type(Spelled.tags[0], StrRef)
assert_type(Spelled.meta["a"], ObjectRef)
assert_type(Spelled.mem_names["a"], nustd.mem.StrRef)
assert_type(Spelled.mem_tags[0], nustd.mem.IntRef)
assert_type(Spelled.by_id.iter().first(), Int)
assert_type(Spelled.mem_tags.iter().first(), Int)
assert_type(Spelled.mem_names.iter().first(), Str)
