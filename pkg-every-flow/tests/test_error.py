"""Tests for TryCatch."""

import pytest

from every_flow import TryCatch, Var
from everybase import Context

from .conftest import Raiser, Recorder


async def test_try_no_error():
    log = []
    tree = TryCatch(Recorder(log, "body"))
    await tree.execute(Context())
    assert log == ["body"]


async def test_try_catch():
    log = []
    tree = TryCatch(
        Raiser(RuntimeError("oops")),
        catch=Recorder(log, "caught"),
    )
    await tree.execute(Context())
    assert log == ["caught"]


async def test_try_catch_with_error_var():
    err = Var("")
    tree = TryCatch(
        Raiser(RuntimeError("some error")),
        catch=Recorder([], "caught"),
        error=err,
    )
    await tree.execute(Context())
    assert err.get() == "some error"


async def test_try_finally_on_success():
    log = []
    tree = TryCatch(
        Recorder(log, "body"),
        finally_=Recorder(log, "finally"),
    )
    await tree.execute(Context())
    assert log == ["body", "finally"]


async def test_try_finally_on_error():
    log = []
    tree = TryCatch(
        Raiser(RuntimeError("fail")),
        catch=Recorder(log, "caught"),
        finally_=Recorder(log, "finally"),
    )
    await tree.execute(Context())
    assert log == ["caught", "finally"]


async def test_try_no_catch_reraises():
    tree = TryCatch(Raiser(RuntimeError("fail")))
    with pytest.raises(RuntimeError, match="fail"):
        await tree.execute(Context())


async def test_try_no_catch_with_finally_still_reraises():
    log = []
    tree = TryCatch(
        Raiser(RuntimeError("fail")),
        finally_=Recorder(log, "finally"),
    )
    with pytest.raises(RuntimeError, match="fail"):
        await tree.execute(Context())
    assert log == ["finally"]


async def test_try_catch_finally_all():
    log = []
    err = Var("")
    tree = TryCatch(
        Raiser(RuntimeError("err")),
        catch=Recorder(log, "caught"),
        finally_=Recorder(log, "finally"),
        error=err,
    )
    await tree.execute(Context())
    assert log == ["caught", "finally"]
    assert err.get() == "err"
