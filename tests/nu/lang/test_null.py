"""Unit tests for ``nu.lang.null``: the NULL contract."""

from __future__ import annotations

import pickle

import pytest

from nu.lang.null import NULL, Null, is_null


def test_null_is_falsy() -> None:
    assert not NULL
    assert not Null("Space.state.recents")


def test_all_nulls_are_equal_whatever_the_hint() -> None:
    assert Null("a.b") == Null("c")
    assert Null("a.b") == NULL
    assert not (Null("a.b") != NULL)


def test_null_is_not_none() -> None:
    assert NULL != None
    assert not (NULL == None)
    assert None != NULL


def test_null_is_not_a_falsy_value() -> None:
    for v in (False, 0, "", [], {}, set()):
        assert NULL != v
        assert v != NULL


def test_hash_ignores_the_hint() -> None:
    assert hash(Null("a")) == hash(Null("b")) == hash(NULL)
    assert len({Null("a"), Null("b"), NULL}) == 1


def test_repr_carries_the_hint() -> None:
    assert repr(NULL) == "<NULL>"
    assert repr(Null("Space.state.recents")) == "<NULL Space.state.recents>"


def test_str_raises() -> None:
    with pytest.raises(TypeError, match=r"Space\.state"):
        str(Null("Space.state"))
    with pytest.raises(TypeError):
        f"{NULL}"


@pytest.mark.parametrize(
    "op",
    [
        len,
        iter,
        lambda n: n + 1,
        lambda n: 1 + n,
        lambda n: -n,
        lambda n: n["k"],
        lambda n: n < 1,
        lambda n: "x" in n,
    ],
)
def test_unsupported_ops_raise_type_error(op: object) -> None:
    with pytest.raises(TypeError):
        op(NULL)  # type: ignore[operator]


def test_is_null() -> None:
    assert is_null(NULL)
    assert is_null(Null("x"))
    for v in (None, False, 0, "", [], object()):
        assert not is_null(v)


def test_pickle_keeps_class_and_hint() -> None:
    back = pickle.loads(pickle.dumps(Null("Space.state.recents")))  # noqa: S301
    assert type(back) is Null
    assert back.hint == "Space.state.recents"
    assert pickle.loads(pickle.dumps(NULL)).hint == ""  # noqa: S301
