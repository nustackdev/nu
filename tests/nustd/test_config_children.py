"""Config a node works with is a child: Print's options, Log's extra, a queue's
capacity, a ui placed op's anchor. None of it is stored on the node besides
its children, so each can be computed in the tree.
"""

from __future__ import annotations

import io
import logging as pylogging

import pytest
from _support.brackets import config

import nu
import nustd
from nu.core.io import STDOUT, Print, StdioBackend
from nu.lang.helpers import arun
from nu.lang.sentinels import UNSET
from nustd.acp.fabric import AcpFabric
from nustd.blob.fabric import BlobFabric
from nustd.cluster.refs import RayServiceRef
from nustd.cluster.resources import RayService
from nustd.logging import Log
from nustd.mp_pool import PoolRef
from nustd.mp_pool.resources import WorkerPool
from nustd.proxy import InvisiblesProxy


class Opts(nu.Shape):
    sep = nu.StrRef.slot()
    tag = nu.StrRef.slot()
    cap = nu.IntRef.slot()


def test_print_options_are_its_last_three_children() -> None:
    node = Print(STDOUT, "a", "b", sep="-", end="!", flush=True)
    assert [c.value for c in nu.tree.children(node)[-3:]] == ["-", "!", True]
    assert not nu.tree.fields(node)


def test_a_print_separator_can_be_read_from_the_tree() -> None:
    out = io.StringIO()
    ctx = nu.Context().bind(StdioBackend, StdioBackend(stdout=out))
    nu.run(nu.Frame(Opts, Print(STDOUT, "a", "b", sep=Opts.sep), sep="+"), ctx)
    assert out.getvalue() == "a+b\n"


def test_log_extra_is_always_the_last_child() -> None:
    plain = Log("info", "nu.t", "hi %s", "x")
    with_extra = Log("info", "nu.t", "hi %s", "x", extra={"k": 1})
    # A mapping is built field by field: an empty one when none was given.
    assert nu.tree.children(nu.tree.children(plain)[-1]) == ()
    assert [c.value for c in nu.tree.children(nu.tree.children(with_extra)[-1])] == [1]
    assert nu.run(nu.tree.children(with_extra)[-1])[0] == {"k": 1}
    # the args sit between msg and extra
    assert [c.value for c in nu.tree.children(with_extra)[4:-1]] == ["x"]


def test_log_extra_reaches_the_record(caplog) -> None:
    with caplog.at_level(pylogging.INFO, logger="nu.t"):
        nu.run(Log("info", "nu.t", "hi %s", "x", extra={"k": 1}))
    (record,) = caplog.records
    assert record.getMessage() == "hi x"
    assert record.k == 1


def test_queue_capacity_is_a_child_after_the_address() -> None:
    class Buf(nu.Shape):
        queue = nustd.queue.JQueueRef.slot(capacity=2, item_type=int)

    assert nu.tree.children(Buf.queue)[2].value == 2
    ctx = nu.Context().bind(dict, {}, Buf)
    q = nu.run(Buf.queue, ctx)[0]
    assert q.maxsize == 2


def test_a_placed_op_anchor_is_its_last_child() -> None:
    lst = nustd.ui.ListRef("l")
    assert nu.tree.children(lst.insert("a", at=0))[-1].value == "at"
    assert nu.tree.children(lst.insert("a", before=2))[-1].value == "before"
    assert nu.tree.children(lst.insert("a"))[-1].value is None
    assert not nu.tree.fields(lst.insert("a", at=0))


def test_log_one_extra_field_can_be_read_from_the_tree(caplog) -> None:
    tree = nu.Frame(Opts, Log("info", "nu.t", "hi", extra={"who": Opts.tag}), tag="computed")
    with caplog.at_level(pylogging.INFO, logger="nu.t"):
        nu.run(tree)
    (record,) = caplog.records
    assert record.who == "computed"


def test_queue_capacity_can_be_read_from_the_tree() -> None:
    class Buf(nu.Shape):
        queue = nustd.queue.JQueueRef.slot(capacity=Opts.cap, item_type=int)

    ctx = nu.Context().bind(dict, {}, Buf)
    q = nu.run(nu.Frame(Opts, Buf.queue, cap=3), ctx)[0]
    assert q.maxsize == 3


# --- a ref's tag or name is a child, so it can be computed -----------------


def _bound(fabric: type, value: object, tag: object) -> nu.Context:
    ctx = nu.Context()
    ctx.fabrics.bind(fabric, value, tag).__enter__()
    return ctx


def test_a_pool_ref_tag_can_be_read_from_the_tree() -> None:
    ctx = _bound(WorkerPool, "gpu-pool", "gpu")
    assert nu.tree.children(PoolRef())[1].value is UNSET
    assert nu.run(nu.Frame(Opts, PoolRef(Opts.tag), tag="gpu"), ctx)[0] == "gpu-pool"
    assert nu.run(PoolRef("gpu"), ctx)[0] == "gpu-pool"


async def test_a_pool_ref_tag_can_be_read_from_the_tree_async() -> None:
    ctx = _bound(WorkerPool, "gpu-pool", "gpu")
    assert (await arun(nu.Frame(Opts, PoolRef(Opts.tag), tag="gpu"), ctx))[0] == "gpu-pool"


def test_a_ray_service_ref_tag_can_be_read_from_the_tree() -> None:
    ctx = _bound(RayService, "ledger", "ledger-main")
    assert nu.tree.children(RayServiceRef())[1].value is UNSET
    tree = nu.Frame(Opts, RayServiceRef(Opts.tag), tag="ledger-main")
    assert nu.run(tree, ctx)[0] == "ledger"
    assert nu.run(RayServiceRef("ledger-main"), ctx)[0] == "ledger"


def test_a_store_ref_name_can_be_read_from_the_tree() -> None:
    ctx = _bound(BlobFabric, "media-backend", "media")
    store = nustd.blob.StoreRef(Opts.tag)
    assert isinstance(store.name, nu.Nu)
    assert nu.run(nu.Frame(Opts, store, tag="media"), ctx)[0] == "media-backend"
    # The computed name is checked when it is evaluated.
    with pytest.raises(TypeError, match="non-empty str"):
        nu.run(nu.Frame(Opts, store, tag=""), ctx)


def test_an_agent_ref_name_can_be_read_from_the_tree() -> None:
    ctx = _bound(AcpFabric, "claude-agent", "claude")
    agent = nustd.acp.AgentRef(Opts.tag)
    assert isinstance(agent.name, nu.Nu)
    assert nu.run(nu.Frame(Opts, agent, tag="claude"), ctx)[0] == "claude-agent"


def test_a_store_ref_preset_binds_under_its_computed_name(tmp_path) -> None:
    # The preset tags the bind with the ref's own name child, so one program
    # binds and reads back under the same computed name.
    store = nustd.blob.StoreRef(Opts.tag)
    app = nu.With(
        nustd.blob.files(store, tmp_path / "files"),
        body=nu.let(store.put(b"hi"), lambda bid: store.get(bid)),
    )
    assert nu.run(nu.Frame(Opts, app, tag="media"))[0] == b"hi"


def test_an_agent_ref_preset_tags_its_bind_with_the_name_child() -> None:
    agent = nustd.acp.AgentRef(Opts.tag)
    spec = nustd.acp.claude(agent, cwd="/srv")
    tags = nu.tree.children(spec)[3]
    assert nu.tree.children(tags)[0] is agent.name
    assert nu.run(nu.Frame(Opts, tags, tag="claude"))[0] == ("claude",)


def test_a_proxy_option_can_be_computed() -> None:
    class Nav:
        pass

    proxy = InvisiblesProxy(Nav, address=nu.Add("127.0.0.1:", "19000"), timeout=nu.Add(1.0, 1.0))
    held = config(proxy)
    assert held["target"] is Nav
    assert held["kwargs"]["address"] == "127.0.0.1:19000"
    assert held["kwargs"]["timeout"] == 2.0
    assert held["kwargs"]["transport"] == "tcp"
