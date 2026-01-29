"""Tests for TryCatch."""

import pytest

from every_flow import TryCatch, Var
from everyabc import Context

from .conftest import Raiser, Recorder


def test_try_no_error():
    log = []
    tree = TryCatch(Recorder(log, "body"))
    tree.execute(Context())
    assert log == ["body"]


def test_try_catch():
    log = []
    tree = TryCatch(
        Raiser(RuntimeError("oops")),
        catch=Recorder(log, "caught"),
    )
    tree.execute(Context())
    assert log == ["caught"]


def test_try_catch_with_error_var():
    err = Var("")
    tree = TryCatch(
        Raiser(RuntimeError("some error")),
        catch=Recorder([], "caught"),
        error=err,
    )
    tree.execute(Context())
    assert err.get() == "some error"


def test_try_finally_on_success():
    log = []
    tree = TryCatch(
        Recorder(log, "body"),
        finally_=Recorder(log, "finally"),
    )
    tree.execute(Context())
    assert log == ["body", "finally"]


def test_try_finally_on_error():
    log = []
    tree = TryCatch(
        Raiser(RuntimeError("fail")),
        catch=Recorder(log, "caught"),
        finally_=Recorder(log, "finally"),
    )
    tree.execute(Context())
    assert log == ["caught", "finally"]


def test_try_no_catch_reraises():
    tree = TryCatch(Raiser(RuntimeError("fail")))
    with pytest.raises(RuntimeError, match="fail"):
        tree.execute(Context())


def test_try_no_catch_with_finally_still_reraises():
    log = []
    tree = TryCatch(
        Raiser(RuntimeError("fail")),
        finally_=Recorder(log, "finally"),
    )
    with pytest.raises(RuntimeError, match="fail"):
        tree.execute(Context())
    assert log == ["finally"]


def test_try_catch_finally_all():
    log = []
    err = Var("")
    tree = TryCatch(
        Raiser(RuntimeError("err")),
        catch=Recorder(log, "caught"),
        finally_=Recorder(log, "finally"),
        error=err,
    )
    tree.execute(Context())
    assert log == ["caught", "finally"]
    assert err.get() == "err"
