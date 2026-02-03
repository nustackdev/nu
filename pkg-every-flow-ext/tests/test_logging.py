"""Tests for Log and Debug."""

import logging

from every_flow import Const
from every_flow_ext import Debug, Log
from everybase import Context


async def test_log_basic(caplog):
    with caplog.at_level(logging.INFO, logger="every_flow_ext"):
        tree = Log("hello world")
        await tree.execute(Context())
    assert "hello world" in caplog.text


async def test_log_with_values(caplog):
    with caplog.at_level(logging.INFO, logger="every_flow_ext"):
        tree = Log("count: {}", [Const(42)])
        await tree.execute(Context())
    assert "count: 42" in caplog.text


async def test_log_level(caplog):
    with caplog.at_level(logging.DEBUG, logger="every_flow_ext"):
        tree = Log("debug msg", level="debug")
        await tree.execute(Context())
    assert "debug msg" in caplog.text


async def test_debug_basic(capsys):
    tree = Debug(Const(1), Const(2), labels=["x", "y"])
    await tree.execute(Context())
    captured = capsys.readouterr()
    assert "x=1" in captured.out
    assert "y=2" in captured.out
    assert "[DEBUG]" in captured.out


async def test_debug_no_labels(capsys):
    tree = Debug(Const("a"))
    await tree.execute(Context())
    captured = capsys.readouterr()
    assert "v0='a'" in captured.out
