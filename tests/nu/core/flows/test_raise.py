"""Raise: a message raised as the class given, and an error handed on as it came."""

from __future__ import annotations

import pytest

import nu


class TaggedError(Exception):
    """An error with a field of its own, so a re-raise can be told from a copy."""

    def __init__(self, msg: str, code: int) -> None:
        super().__init__(msg)
        self.code = code


def _boom() -> None:
    raise TaggedError("boom", 7)


Boom = nu.host(_boom, name="Boom", base=nu.ScalarQuery)


def test_a_message_raises_as_the_class_given():
    with pytest.raises(ValueError, match="bad"):
        nu.run(nu.raise_(ValueError, "bad"))


def test_a_caught_error_is_raised_as_it_came():
    tree = nu.TryCatch(Boom(), catch=lambda err: nu.Raise(err))
    with pytest.raises(TaggedError) as caught:
        nu.run(tree)
    assert caught.value.code == 7


async def test_a_caught_error_is_raised_as_it_came_on_the_loop():
    tree = nu.TryCatch(Boom(), catch=lambda err: nu.Raise(err))
    with pytest.raises(TaggedError) as caught:
        await nu.arun(tree)
    assert caught.value.code == 7


def test_an_exception_value_is_raised_itself():
    err = TaggedError("kept", 3)
    with pytest.raises(TaggedError) as caught:
        nu.run(nu.Raise(nu.Literal(err), exc_cls=RuntimeError))
    assert caught.value is err
