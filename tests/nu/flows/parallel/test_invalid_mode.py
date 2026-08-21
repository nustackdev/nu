"""Construction-time validation of the (child, mode) tuple syntax on Parallel.

Bad mode strings and bad tuple shapes fail at ``__init__``, not at compile
or run - so misuse surfaces where the tree is being built. Only ``Parallel``
(and its forced-mode variants) accept the tuple syntax.
"""

from __future__ import annotations

import pytest

from nu.context import AttrRef, SetCmd
from nu.core import Literal
from nu.flows import Parallel


def _set(name: str, value: object) -> SetCmd:
    return SetCmd(AttrRef(name), Literal(value))


def test_bad_mode_string_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Parallel child mode must be"):
        Parallel((_set("a", 1), "banana"))


def test_non_string_mode_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Parallel child mode must be"):
        Parallel((_set("a", 1), 42))


def test_wrong_tuple_shape_raises_type_error() -> None:
    with pytest.raises(TypeError, match="Parallel child override must be"):
        Parallel((_set("a", 1), "threaded", "extra"))


def test_first_tuple_element_must_be_nu() -> None:
    with pytest.raises(TypeError, match="Parallel child override must be"):
        Parallel(("not a nu", "threaded"))


def test_non_nu_non_tuple_child_rejected() -> None:
    with pytest.raises(TypeError, match="child must be a Nu instance"):
        Parallel(42)


def test_mixed_tuple_and_plain_construction_ok() -> None:
    # Sanity: mixing bare and tuple forms constructs without error.
    tree = Parallel((_set("a", 1), "async"), _set("b", 2))
    assert tree._payload["parallel_modes"] == ("async", None)
