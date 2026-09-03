"""Tests for nu.info.core.source - what the code says, in isolation."""

from __future__ import annotations

import types

from nu.info.core.source import (
    public_members,
    read_location,
    read_signature,
    read_source,
    unpacked_count,
)


# --- signature -----------------------------------------------------------


def test_signature_of_a_plain_function() -> None:
    def target(a: int, b: str = "x", *rest: int, flag: bool = False, **kw: int) -> None: ...

    sig = read_signature(target)
    assert sig is not None
    assert [p.name for p in sig.positional] == ["a", "b"]
    assert [p.name for p in sig.keyword] == ["flag"]
    assert sig.required == 1
    assert sig.variadic and sig.keyword_variadic


def test_signature_of_a_class_reads_init_and_drops_self() -> None:
    class Target:
        def __init__(self, first: object, second: object = None) -> None: ...

    sig = read_signature(Target)
    assert sig is not None
    assert [p.name for p in sig.params] == ["first", "second"]
    assert sig.render("Target") == "Target(first, second=None)"


def test_signature_detects_classmethod_and_staticmethod() -> None:
    class Target:
        @classmethod
        def made(cls) -> None: ...

        @staticmethod
        def free() -> None: ...

    assert read_signature(Target.made).is_classmethod
    assert read_signature(vars(Target)["free"]).is_staticmethod


def test_signature_of_an_unreadable_callable_is_none() -> None:
    assert read_signature(3) is None


# --- module --------------------------------------------------------------


def _module(name: str, **members: object) -> types.ModuleType:
    mod = types.ModuleType(name)
    for key, value in members.items():
        setattr(mod, key, value)
    return mod


def test_module_uses_all_when_declared() -> None:
    mod = _module("m", a=1, b=2, __all__=["a"])
    assert [m.name for m in public_members(mod)] == ["a"]


def test_module_without_all_keeps_own_names_only() -> None:
    class Own:
        pass

    class Elsewhere:
        pass

    Own.__module__ = "m"
    Elsewhere.__module__ = "other"
    mod = _module("m", Own=Own, Elsewhere=Elsewhere, _private=object())
    assert [m.name for m in public_members(mod)] == ["Own"]


def test_module_dedupes_by_identity_and_records_aliases() -> None:
    target = object()
    mod = _module("m", one=target, two=target, __all__=["one", "two"])
    (member,) = public_members(mod)
    assert member.name == "one"
    assert member.aliases == ("two",)


def test_module_skips_submodules() -> None:
    mod = _module("m", sub=types.ModuleType("sub"), value=1, __all__=["sub", "value"])
    assert [m.name for m in public_members(mod)] == ["value"]


# --- code ----------------------------------------------------------------


def test_source_reads_text_and_location() -> None:
    source = read_source(read_signature)
    assert source is not None
    assert source.text.startswith("def read_signature")
    assert source.file.endswith("signature.py")
    assert source.line > 0


def test_source_of_an_unreadable_object_is_none() -> None:
    assert read_source(42) is None
    assert read_location(42) is None


# --- unpack --------------------------------------------------------------


def test_unpacked_count_reads_the_widest_unpack() -> None:
    def one(children: tuple[object, ...]) -> object:
        (only,) = children
        return only

    def either(children: tuple[object, ...]) -> object:
        if len(children) == 1:
            (only,) = children
            return only
        left, right = children
        return left, right

    def never(children: tuple[object, ...]) -> object:
        return children

    assert unpacked_count(one, "children") == 1
    assert unpacked_count(either, "children") == 2
    assert unpacked_count(never, "children") is None
    assert unpacked_count(one, "other") is None
