"""Tests for Log and Debug."""

import logging

from every_flow import Const
from every_flow_ext import Debug, Log
from everyabc import Context


def test_log_basic(caplog):
    with caplog.at_level(logging.INFO, logger="every_flow_ext"):
        tree = Log("hello world")
        tree.execute(Context())
    assert "hello world" in caplog.text


def test_log_with_values(caplog):
    with caplog.at_level(logging.INFO, logger="every_flow_ext"):
        tree = Log("count: {}", [Const(42)])
        tree.execute(Context())
    assert "count: 42" in caplog.text


def test_log_level(caplog):
    with caplog.at_level(logging.DEBUG, logger="every_flow_ext"):
        tree = Log("debug msg", level="debug")
        tree.execute(Context())
    assert "debug msg" in caplog.text


def test_debug_basic(capsys):
    tree = Debug(Const(1), Const(2), labels=["x", "y"])
    tree.execute(Context())
    captured = capsys.readouterr()
    assert "x=1" in captured.out
    assert "y=2" in captured.out
    assert "[DEBUG]" in captured.out


def test_debug_no_labels(capsys):
    tree = Debug(Const("a"))
    tree.execute(Context())
    captured = capsys.readouterr()
    assert "v0='a'" in captured.out
