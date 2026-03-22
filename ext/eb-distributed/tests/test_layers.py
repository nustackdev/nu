"""Integration tests - layer by layer, bottom-up.

Layer 1: Direct (no proxy) - local Navigator, write/read
Layer 2: Single proxy - Navigator in subprocess, write/read through proxy
Layer 3: Worker in-process, local storage - tree execution via Worker.execute()
Layer 4: Worker in-process, proxied storage - tree execution, Navigator in subprocess
Layer 5: Worker in subprocess, local storage - tree sent via RPC
Layer 6: Worker in subprocess, proxied storage - full distributed

Each layer adds exactly one level of complexity.
"""

import pytest
from composables import Runtime
from composables.spec import SpecBuilder
from virtuals import Navigator

import eb_virtuals as ebv
import everybase
from eb_distributed import (
    ContextSpec,
    InvisiblesClientSpec,
    NavigatorSpec,
    ProcessLauncherSpec,
    Teleport,
    Worker,
    WorkerSpec,
)
from everybase import Context
from everybase.abc import Seq

from .conftest import TestShape


# ============================================================================
# Helpers
# ============================================================================


class AssertNotEmpty(everybase.UnaryOperation):
    """Term that asserts its operand is not EMPTY/INVALID. Raises on sentinel."""

    def apply(self, value):
        if everybase.is_sentinel(value):
            raise AssertionError(f"Expected a value, got sentinel: {value}")
        return value


# ============================================================================
# Flow factory (fresh per test to avoid cross-test netref pollution)
# ============================================================================


def make_store_and_verify_flow():
    """Create a fresh flow each time to avoid stale netref leaks between tests."""
    return ebv.Transaction(
        Seq(
            TestShape.price.store(42.0),
            TestShape.quantity.store(10),
            AssertNotEmpty(TestShape.price),
            AssertNotEmpty(TestShape.quantity),
        )
    )


# ============================================================================
# Layer 1: Direct - no proxy, no subprocess
# ============================================================================


class TestLayer1Direct:
    """Local Navigator, local storage, direct execution."""

    @pytest.mark.asyncio
    async def test_manual_write_read(self):
        """Manual view write/read without everybase tree."""
        async with Runtime() as rt:
            nav = await rt.create(NavigatorSpec())
            txn = nav.storage.begin_transaction()
            view = nav.root(txn)

            view["price"] = 42.0
            assert view["price"] == 42.0

            txn.commit()

    @pytest.mark.asyncio
    async def test_tree_execution(self):
        """Tree execution with Transaction span."""
        async with Runtime() as rt:
            ctx_res = await rt.create(ContextSpec())
            await make_store_and_verify_flow().execute(ctx_res.ctx)

    @pytest.mark.asyncio
    async def test_context_navigator_binding(self):
        """Verify Navigator is bound in context and resolvable."""
        async with Runtime() as rt:
            ctx_res = await rt.create(ContextSpec())
            nav = ctx_res.ctx[Navigator,]
            assert nav is not None
            assert hasattr(nav, "root")
            assert hasattr(nav, "storage")


# ============================================================================
# Layer 2: Single proxy - Navigator in subprocess
# ============================================================================


class TestLayer2SingleProxy:
    """Navigator in subprocess via RPC. Write/read through proxy."""

    @pytest.fixture
    def proxied_nav_spec(self, sock):
        nav_spec = NavigatorSpec()
        return (
            SpecBuilder(nav_spec)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=sock))
            .with_launcher(ProcessLauncherSpec(transport="unix", address=sock))
            .build()
        )

    @pytest.mark.asyncio
    async def test_manual_write_read(self, proxied_nav_spec):
        """Manual view write/read through proxied Navigator."""
        async with Runtime() as rt:
            nav = await rt.create(proxied_nav_spec)
            txn = nav.storage.begin_transaction()
            view = nav.root(txn)

            view["price"] = 42.0
            assert view["price"] == 42.0

            txn.commit()

    @pytest.mark.asyncio
    async def test_tree_execution(self, proxied_nav_spec):
        """Tree execution through proxied Navigator."""
        async with Runtime() as rt:
            ctx_res = await rt.create(ContextSpec(storage=proxied_nav_spec))
            await make_store_and_verify_flow().execute(ctx_res.ctx)

    @pytest.mark.asyncio
    async def test_context_navigator_binding(self, proxied_nav_spec):
        """Navigator proxy is correctly bound in context."""
        async with Runtime() as rt:
            ctx_res = await rt.create(ContextSpec(storage=proxied_nav_spec))
            nav = ctx_res.ctx[Navigator,]
            assert nav is not None


# ============================================================================
# Layer 3: Worker in-process, local storage
# ============================================================================


class TestLayer3WorkerInProcessLocal:
    """Worker runs in-process with its own local storage."""

    @pytest.mark.asyncio
    async def test_worker_execute(self):
        """Worker.execute() runs tree against its own context."""
        async with Runtime() as rt:
            worker = await rt.create(WorkerSpec())
            await worker.execute(make_store_and_verify_flow())

    @pytest.mark.asyncio
    async def test_teleport(self):
        """Teleport ships subtree to in-process Worker."""
        async with Runtime() as rt:
            worker = await rt.create(WorkerSpec(name="w0"))
            ctx = Context().bind(worker, Worker, 0)
            await Teleport(make_store_and_verify_flow(), worker=0).execute(ctx)


# ============================================================================
# Layer 4: Worker in-process, proxied storage
# ============================================================================


class TestLayer4WorkerInProcessProxiedStorage:
    """Worker runs in-process, Navigator in subprocess via RPC."""

    @pytest.fixture
    def specs(self, sock):
        nav_spec = NavigatorSpec()
        state_spec = (
            SpecBuilder(nav_spec)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=sock))
            .with_launcher(
                ProcessLauncherSpec(
                    transport="unix",
                    address=sock,
                    executor="threaded",
                )
            )
            .build()
        )
        worker_nav_spec = (
            SpecBuilder(nav_spec)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=sock))
            .build()
        )
        return state_spec, WorkerSpec(context=ContextSpec(storage=worker_nav_spec))

    @pytest.mark.asyncio
    async def test_manual_worker_nav(self, specs):
        """Worker's Navigator proxy works for manual write/read."""
        state_spec, worker_spec = specs
        async with Runtime() as rt:
            await rt.create(state_spec)
            worker = await rt.create(worker_spec)

            nav = worker.context.storage
            txn = nav.storage.begin_transaction()
            view = nav.root(txn)
            view["test"] = "hello"
            assert view["test"] == "hello"
            txn.commit()

    @pytest.mark.asyncio
    async def test_worker_execute(self, specs):
        """Worker.execute() with proxied Navigator."""
        state_spec, worker_spec = specs
        async with Runtime() as rt:
            await rt.create(state_spec)
            worker = await rt.create(worker_spec)
            await worker.execute(make_store_and_verify_flow())

    @pytest.mark.asyncio
    async def test_teleport(self, specs):
        """Teleport to in-process Worker with proxied Navigator."""
        state_spec, worker_spec = specs
        async with Runtime() as rt:
            await rt.create(state_spec)
            worker = await rt.create(worker_spec)
            ctx = Context().bind(worker, Worker, 0)
            await Teleport(make_store_and_verify_flow(), worker=0).execute(ctx)


# ============================================================================
# Layer 5: Worker in subprocess, local storage
# ============================================================================


class TestLayer5WorkerSubprocessLocal:
    """Worker in subprocess via RPC, with its own local storage."""

    @pytest.fixture
    def subprocess_worker_spec(self, sock):
        return (
            SpecBuilder(WorkerSpec())
            .as_proxy(InvisiblesClientSpec(transport="unix", address=sock))
            .with_launcher(
                ProcessLauncherSpec(
                    transport="unix",
                    address=sock,
                    dispatcher="async",
                )
            )
            .build()
        )

    @pytest.mark.asyncio
    async def test_worker_execute(self, subprocess_worker_spec):
        """Tree sent to subprocess Worker, executed with local storage."""
        async with Runtime() as rt:
            worker = await rt.create(subprocess_worker_spec)
            await worker.execute(make_store_and_verify_flow())

    @pytest.mark.asyncio
    async def test_teleport(self, subprocess_worker_spec):
        """Teleport to subprocess Worker with local storage."""
        async with Runtime() as rt:
            worker = await rt.create(subprocess_worker_spec)
            ctx = Context().bind(worker, Worker, 0)
            await Teleport(make_store_and_verify_flow(), worker=0).execute(ctx)


# ============================================================================
# Layer 6: Worker in subprocess, proxied storage (full distributed)
# ============================================================================


class TestLayer6FullDistributed:
    """Worker in subprocess, Navigator in separate subprocess. The full picture."""

    @pytest.fixture
    def specs(self, sock):
        state_sock = sock + "-state"
        worker_sock = sock + "-w0"
        nav_spec = NavigatorSpec()

        state_spec = (
            SpecBuilder(nav_spec)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=state_sock))
            .with_launcher(
                ProcessLauncherSpec(
                    transport="unix",
                    address=state_sock,
                    executor="threaded",
                )
            )
            .build()
        )

        worker_nav = (
            SpecBuilder(nav_spec)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=state_sock))
            .build()
        )

        worker_spec = (
            SpecBuilder(WorkerSpec(context=ContextSpec(storage=worker_nav)))
            .as_proxy(InvisiblesClientSpec(transport="unix", address=worker_sock))
            .with_launcher(
                ProcessLauncherSpec(
                    transport="unix",
                    address=worker_sock,
                    dispatcher="async",
                )
            )
            .build()
        )

        return state_spec, worker_spec

    @pytest.mark.asyncio
    async def test_worker_execute(self, specs):
        """Tree execution on subprocess Worker with proxied Navigator."""
        state_spec, worker_spec = specs
        async with Runtime() as rt:
            await rt.create(state_spec)
            worker = await rt.create(worker_spec)
            await worker.execute(make_store_and_verify_flow())

    @pytest.mark.asyncio
    async def test_teleport(self, specs):
        """Teleport to subprocess Worker with proxied Navigator."""
        state_spec, worker_spec = specs
        async with Runtime() as rt:
            await rt.create(state_spec)
            worker = await rt.create(worker_spec)
            ctx = Context().bind(worker, Worker, 0)
            await Teleport(make_store_and_verify_flow(), worker=0).execute(ctx)

    @pytest.mark.asyncio
    async def test_parallel_teleport(self, sock):
        """Two subprocess Workers, parallel Teleport, shared storage."""
        from everybase.abc.flows.parallel import Parallel

        state_sock = sock + "-state"
        w0_sock = sock + "-w0"
        w1_sock = sock + "-w1"
        nav_spec = NavigatorSpec()

        state_spec = (
            SpecBuilder(nav_spec)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=state_sock))
            .with_launcher(
                ProcessLauncherSpec(
                    transport="unix",
                    address=state_sock,
                    executor="threaded",
                )
            )
            .build()
        )

        worker_nav = (
            SpecBuilder(nav_spec)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=state_sock))
            .build()
        )
        worker_base = WorkerSpec(context=ContextSpec(storage=worker_nav))

        w0_spec = (
            SpecBuilder(worker_base)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=w0_sock))
            .with_launcher(
                ProcessLauncherSpec(
                    transport="unix",
                    address=w0_sock,
                    dispatcher="async",
                )
            )
            .build()
        )
        w1_spec = (
            SpecBuilder(worker_base)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=w1_sock))
            .with_launcher(
                ProcessLauncherSpec(
                    transport="unix",
                    address=w1_sock,
                    dispatcher="async",
                )
            )
            .build()
        )

        flow = Parallel(
            Teleport(
                ebv.Transaction(
                    Seq(
                        TestShape.price.store(100.0),
                        AssertNotEmpty(TestShape.price),
                    )
                ),
                worker=0,
            ),
            Teleport(
                ebv.Transaction(
                    Seq(
                        TestShape.quantity.store(5),
                        AssertNotEmpty(TestShape.quantity),
                    )
                ),
                worker=1,
            ),
        )

        async with Runtime() as rt:
            await rt.create(state_spec)
            w0 = await rt.create(w0_spec)
            w1 = await rt.create(w1_spec)
            ctx = Context().bind(w0, Worker, 0).bind(w1, Worker, 1)
            await flow.execute(ctx)
