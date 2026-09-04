"""Tests for ``nu.std.logging`` -- Python's ``logging`` module, wrapped as Nu.

Every ``log.info(...)`` / ``logging.info(...)`` call returns a ``Log``
tree that, when driven, calls into Python's ``logging`` machinery. Tests use
pytest's ``caplog`` fixture -- the idiomatic Python way to assert on log
records -- so we exercise the same handlers/formatters the user would.
"""

from __future__ import annotations

import asyncio
import logging as pylogging
from typing import TYPE_CHECKING

from nu import Context, arun, run
from nu.lang import Cardinality, Sort
from nu.lang.attributes import Attr, Effect
from nu.lang.helpers import compile
from nu.std import logging
from nu.std.logging import LOGGING, Log, LoggingRef


if TYPE_CHECKING:
    import pytest


# --- API surface: mirror of Python's logging ---------------------------------


def test_getLogger_returns_a_bound_Logger() -> None:  # noqa: N802
    log = logging.getLogger("nu.test")
    assert isinstance(log, logging.Logger)
    assert log.name == "nu.test"


def test_getLogger_with_no_arg_returns_root() -> None:  # noqa: N802
    assert logging.getLogger().name == "root"
    assert logging.getLogger(None).name == "root"


def test_level_constants_match_stdlib() -> None:
    assert logging.DEBUG == pylogging.DEBUG
    assert logging.INFO == pylogging.INFO
    assert logging.WARNING == pylogging.WARNING
    assert logging.WARN == pylogging.WARNING
    assert logging.ERROR == pylogging.ERROR
    assert logging.CRITICAL == pylogging.CRITICAL
    assert logging.FATAL == pylogging.CRITICAL


def test_logger_methods_return_log_commands() -> None:
    log = logging.getLogger("nu.test")
    assert isinstance(log.debug("x"), Log)
    assert isinstance(log.info("x"), Log)
    assert isinstance(log.warning("x"), Log)
    assert isinstance(log.warn("x"), Log)  # stdlib alias
    assert isinstance(log.error("x"), Log)
    assert isinstance(log.critical("x"), Log)
    assert isinstance(log.fatal("x"), Log)  # stdlib alias
    assert isinstance(log.log(pylogging.INFO, "x"), Log)


def test_module_level_shortcuts_return_log_commands() -> None:
    assert isinstance(logging.debug("x"), Log)
    assert isinstance(logging.info("x"), Log)
    assert isinstance(logging.warning("x"), Log)
    assert isinstance(logging.warn("x"), Log)
    assert isinstance(logging.error("x"), Log)
    assert isinstance(logging.critical("x"), Log)
    assert isinstance(logging.log(pylogging.INFO, "x"), Log)


# --- structure & sorts -------------------------------------------------------


def test_log_command_is_a_command() -> None:
    assert Log._sort.value is Sort.SCALAR_COMMAND


def test_log_command_yields_nothing() -> None:
    assert Log._cardinality.value is Cardinality.VOID


def test_log_command_slots_hold_the_fabric_ref() -> None:
    log = logging.getLogger("nu.test")
    cmd = log.info("hello")
    # slot 0 is the LOGGING fabric singleton
    assert cmd._children[0] is LOGGING


def test_log_command_declares_write_through_logging_ref() -> None:
    program = compile(logging.info("x"))
    effects = program.attr((), Attr.COMPOSITION_EFFECTS)
    assert (LoggingRef, Effect.WRITE) in effects


# --- functional: records reach Python's logging module ----------------------


def test_info_emits_a_log_record(caplog: pytest.LogCaptureFixture) -> None:
    log = logging.getLogger("nu.test")
    caplog.set_level(pylogging.DEBUG, logger="nu.test")
    run(log.info("hello world"))
    assert [(r.levelno, r.name, r.getMessage()) for r in caplog.records] == [
        (pylogging.INFO, "nu.test", "hello world"),
    ]


def test_percent_formatting_of_msg_args(caplog: pytest.LogCaptureFixture) -> None:
    log = logging.getLogger("nu.test")
    caplog.set_level(pylogging.DEBUG, logger="nu.test")
    run(log.error("slot %s failed after %s attempts", 42, 5))
    assert caplog.records[0].getMessage() == "slot 42 failed after 5 attempts"
    assert caplog.records[0].levelno == pylogging.ERROR


def test_extra_fields_ride_on_the_log_record(caplog: pytest.LogCaptureFixture) -> None:
    log = logging.getLogger("nu.test")
    caplog.set_level(pylogging.DEBUG, logger="nu.test")
    run(log.warning("checkout failed", extra={"code": 500, "user": "u42"}))
    rec = caplog.records[0]
    assert rec.code == 500  # extras are set as attributes on the LogRecord
    assert rec.user == "u42"


def test_each_level_routes_to_its_python_level(caplog: pytest.LogCaptureFixture) -> None:
    log = logging.getLogger("nu.test")
    caplog.set_level(pylogging.DEBUG, logger="nu.test")
    run(log.debug("d"))
    run(log.info("i"))
    run(log.warning("w"))
    run(log.error("e"))
    run(log.critical("c"))
    levels = [r.levelno for r in caplog.records]
    assert levels == [
        pylogging.DEBUG,
        pylogging.INFO,
        pylogging.WARNING,
        pylogging.ERROR,
        pylogging.CRITICAL,
    ]


def test_string_level_names_are_accepted(caplog: pytest.LogCaptureFixture) -> None:
    # Log normalizes str level names to Python ints -- so a rewrite
    # that carries level names as literals still routes to the right level.
    caplog.set_level(pylogging.DEBUG, logger="nu.test")
    run(Log("warning", "nu.test", "hello"))
    assert caplog.records[0].levelno == pylogging.WARNING


def test_async_path_emits_record(caplog: pytest.LogCaptureFixture) -> None:
    log = logging.getLogger("nu.test")
    caplog.set_level(pylogging.DEBUG, logger="nu.test")
    asyncio.run(arun(log.info("async %s", "hi")))
    assert caplog.records[0].getMessage() == "async hi"


def test_module_level_info_uses_root_logger(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(pylogging.DEBUG, logger="root")
    run(logging.info("root-level"))
    assert caplog.records[0].name == "root"
    assert caplog.records[0].getMessage() == "root-level"


def test_msg_can_be_a_nu_term(caplog: pytest.LogCaptureFixture) -> None:
    # Log accepts Nu terms in the msg + args slots; refs resolve at
    # eval time. Uses a bound AttrRef for a real test.
    from nu.context import StrAttrRef

    log = logging.getLogger("nu.test")
    caplog.set_level(pylogging.DEBUG, logger="nu.test")

    ctx = Context()
    ctx.attrs["who"] = "gor"
    run(log.info("hi %s", StrAttrRef("who")), ctx)
    assert caplog.records[0].getMessage() == "hi gor"


def test_msg_skips_on_unbound_sentinel(caplog: pytest.LogCaptureFixture) -> None:
    # An unbound attr reads EMPTY -- the whole line is dropped rather than
    # emitting a partially-formatted string.
    from nu.context import StrAttrRef

    log = logging.getLogger("nu.test")
    caplog.set_level(pylogging.DEBUG, logger="nu.test")
    run(log.info("hi %s", StrAttrRef("missing")))
    assert caplog.records == []


# --- fabric identity ---------------------------------------------------------


def test_logging_singleton_is_a_logging_ref() -> None:
    assert isinstance(LOGGING, LoggingRef)
    # repr comes from nu.lang.render; LoggingRef carries no payload.
    assert repr(LOGGING) == "LoggingRef"
