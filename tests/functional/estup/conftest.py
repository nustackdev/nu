"""Fixtures for estup functional tests."""

from __future__ import annotations

import pytest
from estup import BinaryKeyCodec, PyBinaryKeyCodec, StringKeyCodec


@pytest.fixture(
    params=[
        pytest.param("binary", id="binary"),
        pytest.param("pybinary", id="pybinary"),
        pytest.param("string", id="string"),
    ],
    scope="session",
)
def codec_type(request):
    """Parametrize codec type."""
    return request.param


@pytest.fixture(scope="session")
def codec(codec_type: str):
    """Create codec instance based on type."""
    if codec_type == "binary":
        return BinaryKeyCodec()
    elif codec_type == "pybinary":
        return PyBinaryKeyCodec()
    elif codec_type == "string":
        return StringKeyCodec()
    else:
        raise ValueError(f"Unknown codec type: {codec_type}")
