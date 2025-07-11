#!/usr/bin/env python3
"""
Concurrent state update test across multiple processes.

Architecture:
/main (process)
├── /coordinator
│   ├── /worker1 (process) → shared_state_service
│   └── /worker2 (process) → shared_state_service
│       └── /shared_state_service (process)
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import attrs
from loomidistributed.launcher._multiprocessing import MultiprocessingLauncherSpec
from loomidistributed.rpc.rpyc import RPyCUnixClientSpec, RPyCUnixConnectionSpec, RPyCUnixServerSpec

from loomicore.attach import Attach, AttachMany, ListCoordinator
from loomicore.resource import SyncResource
from loomicore.spec import ProxySpec, Spec
from loomistd.kv.lmdb import LMDBStorageSpec
from loomistd.state import StateService, StateSpec
from loomix.logging import setup_logging

setup_logging(".logs", log_level=20)


# 1. StateWorker - performs rapid state updates
class StateWorker(SyncResource):
    spec: StateWorkerSpec
    state_service: StateService = Attach()

    def run_updates(self):
        start_time = time.time()
        state = self.state_service.state

        with state.at("results").with_dict_view() as results:
            print(f"Worker {self.spec.worker_id} starting updates...")
            for i in range(self.spec.update_count):
                print(f"Worker {self.spec.worker_id} updating {i + 1}/{self.spec.update_count}...")
                results.set(f"{self.spec.worker_id}_{i}", self.spec.worker_id + f"_{i}")

        print(f"Worker {self.spec.worker_id} completed updates in {time.time() - start_time:.3f}s")

        print(f"Worker {self.spec.worker_id} results:")
        with state.at("results").with_dict_view() as results:
            print(results.extract())


@attrs.define(frozen=True, slots=True, kw_only=True)
class StateWorkerSpec(Spec):
    name: str = "state_worker"
    factory: type = StateWorker
    state_spec: ProxySpec
    worker_id: str
    update_count: int = 1000
    state_service: Spec


# 2. MainCoordinator - orchestrates multiple workers
class MainCoordinator(SyncResource):
    spec: MainCoordinatorSpec
    workers: ListCoordinator[StateWorker] = AttachMany()

    def execute_concurrent_updates(self):
        def run_worker(worker):
            return worker.run_updates()

        for w in self.workers:
            print(f"Starting updates for {w.spec.worker_id}...")

        start_time = time.time()

        # Execute both workers concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.map(run_worker, self.workers)

        total_duration = time.time() - start_time

        print("\n🏁 Performance Results:")
        print(f"Total duration: {total_duration:.3f}s")


@attrs.define(frozen=True, slots=True, kw_only=True)
class MainCoordinatorSpec(Spec):
    name: str = "main_coordinator"
    factory: type = MainCoordinator
    workers: tuple[ProxySpec]


def main():
    print("🚀 Starting concurrent state update test")

    # Shared state specification
    lmdb_state_spec = StateSpec(
        storage=LMDBStorageSpec(),
    ).with_value_at("storage", "path", value=".tplgl")
    file_state_spec = StateSpec().with_value_at("storage", "path", value=".tplgf")

    state_spec = lmdb_state_spec

    shared_state_spec = ProxySpec(
        inner_spec=state_spec,
        client_spec=RPyCUnixClientSpec(
            connection=RPyCUnixConnectionSpec(socket_path="/tmp/shared_state_lmdb_test.sock")
        ),
        launcher_spec=MultiprocessingLauncherSpec(
            host=RPyCUnixServerSpec(socket_path="/tmp/shared_state_lmdb_test.sock")
        ),
    )
    shared_state_spec_no_launcher = ProxySpec(
        inner_spec=state_spec,
        client_spec=RPyCUnixClientSpec(
            connection=RPyCUnixConnectionSpec(socket_path="/tmp/shared_state_lmdb_test.sock")
        ),
    )

    # Worker1 specification with dedicated socket
    worker1_spec = ProxySpec(
        inner_spec=StateWorkerSpec(
            state_spec=shared_state_spec,
            worker_id="worker1",
            state_service=shared_state_spec,
        ),
        client_spec=RPyCUnixClientSpec(
            connection=RPyCUnixConnectionSpec(socket_path="/tmp/worker1_launcher.sock")
        ),
        launcher_spec=MultiprocessingLauncherSpec(
            host=RPyCUnixServerSpec(socket_path="/tmp/worker1_launcher.sock")
        ),
    )

    # Worker2 specification with dedicated socket
    worker2_spec = ProxySpec(
        inner_spec=StateWorkerSpec(
            state_spec=shared_state_spec,
            worker_id="worker2",
            state_service=shared_state_spec_no_launcher,
        ),
        client_spec=RPyCUnixClientSpec(
            connection=RPyCUnixConnectionSpec(socket_path="/tmp/worker2_launcher.sock")
        ),
        launcher_spec=MultiprocessingLauncherSpec(
            host=RPyCUnixServerSpec(socket_path="/tmp/worker2_launcher.sock")
        ),
    )

    # Main coordinator specification
    coordinator_spec = MainCoordinatorSpec(
        workers=tuple([worker1_spec, worker2_spec]),
    )

    # Execute the test
    with MainCoordinator(coordinator_spec) as coordinator:
        coordinator.execute_concurrent_updates()

    print("✅ Test completed")


if __name__ == "__main__":
    main()
