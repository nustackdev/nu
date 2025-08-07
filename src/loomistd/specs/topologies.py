"""
Topology Specs

Provides high-level topology functions that return complete, ready-to-deploy
application specifications. Each topology encapsulates storage strategy,
communication patterns, process management.

Named after actual Star Trek starships:
- Enterprise NCC-1701-D: Flagship, reliable, production-ready
- Defiant NX-74205: Fast, combat-ready, low-latency
- Voyager NCC-74656: Long-running, exploration workloads
- Cerritos NCC-75567: Simple, utility work, development
"""

from __future__ import annotations

from loomi import AppSpec, Spec, SpecBuilder
from loomistd.runtime import RuntimeSpec

from .launcher import get_launcher_spec
from .rpc import get_rpyc_specs
from .state import get_file_state_spec, get_lmdb_state_spec

__all__ = [
    "get_enterprise_d_topology",
    "get_enterprise_d_file_topology",
    "get_defiant_topology",
    "get_voyager_topology",
    "get_cerritos_topology",
]


def get_enterprise_d_topology(
    app_spec: AppSpec,
    *,
    worker_count: int = 4,
    storage_path: str = ".db",
    socket_base: str = "/tmp/enterprise",
    app_name: str = "enterprise_app",
) -> Spec:
    """
    Create an Enterprise NCC-1701-D topology for production deployments.

    Like the flagship USS Enterprise NCC-1701-D - reliable, robust,
    production-ready. The Galaxy-class flagship represents the best of
    Starfleet engineering with proven, battle-tested systems.

    Features LMDB persistent storage, Unix socket communication,
    multiprocessing workers, and proven architectural patterns.

    Perfect for:
    - Production applications
    - Reliable distributed processing
    - General-purpose workloads
    - Systems requiring persistence

    Registry: NCC-1701-D (Galaxy-class)
    Captain: Jean-Luc Picard

    Args:
        app_spec_class: Application spec class to deploy
        worker_count: Number of worker processes (default: 4)
        storage_path: Path for LMDB storage (default: ".db_msgpack")
        socket_base: Base path for Unix sockets (default: "/tmp/enterprise")
        app_name: Name for the main application (default: "enterprise_app")
        **kwargs: Additional arguments passed to app_spec_class

    Returns:
        Complete application spec ready for deployment

    Examples:
        ```python
        # Basic Enterprise deployment
        app = get_enterprise_topology(MyAppSpec)

        # Production trading system
        trading_app = get_enterprise_topology(
            TradingAppSpec,
            worker_count=8,
            storage_path="/data/trading.db",
            socket_base="/tmp/trading"
        )

        # Deploy the flagship
        with MyApp(app) as system:
            system.evaluate(system.define(), Context(None))
        ```
    """

    # 1. Create base state with LMDB persistence
    base_state = get_lmdb_state_spec(path=storage_path, mode="write", name=f"{app_name}_state")

    # 2. Create RPC specs for state service
    state_client, state_server = get_rpyc_specs(
        rpc_type="unix",
        address=f"{socket_base}_state.sock",
        client_name=f"{app_name}_state_client",
        server_name=f"{app_name}_state_server",
    )

    # 3. Create proxied state with launcher capability
    proxied_state = (
        SpecBuilder(base_state)
        .as_proxy(state_client)
        .with_launcher(
            get_launcher_spec(
                host=state_server,
                launcher_type="multiprocessing",
                name=f"{app_name}_state_launcher",
            )
        )
        .build()
    )

    # 4. Create proxy state for workers (without launcher)
    proxy_state_for_workers = SpecBuilder(base_state).as_proxy(state_client).build()

    # 5. Create base worker app spec
    base_worker = app_spec.with_value_at("state", value=proxy_state_for_workers).with_value_at(
        "name", value="worker"
    )

    # 6. Create worker fleet with replication
    worker_client, worker_server = get_rpyc_specs(
        rpc_type="unix",
        address=f"{socket_base}_worker.sock",
        client_name="worker_client",
        server_name="worker_server",
    )

    worker_fleet = (
        SpecBuilder(base_worker)
        .as_proxy(worker_client)
        .with_launcher(
            get_launcher_spec(
                host=worker_server, launcher_type="multiprocessing", name="worker_launcher"
            )
        )
        .replicate(
            count=worker_count,
            paths={
                ("client_spec", "connection", "socket_path"): f"{socket_base}_worker_{{}}.sock",
                ("launcher_spec", "host", "socket_path"): f"{socket_base}_worker_{{}}.sock",
                ("inner_spec", "name"): "worker_{}",
                ("client_spec", "name"): "worker_{}_client",
                ("launcher_spec", "name"): "worker_{}_launcher",
            },
        )
    )

    # 7. Create runtime with worker fleet
    runtime = RuntimeSpec(fleet=tuple(worker_fleet), name=f"{app_name}_runtime")

    # 8. Create main application spec
    main_app = app_spec.with_value_at(
        "state",
        value=proxied_state,
    ).with_value_at(
        "runtime",
        value=runtime,
    )

    return main_app


def get_enterprise_d_file_topology(
    app_spec: AppSpec,
    *,
    worker_count: int = 4,
    storage_path: str = ".data",
    socket_base: str = "/tmp/enterprise_file",
    app_name: str = "enterprise_file_app",
) -> Spec:
    """
    Create an Enterprise NCC-1701-D topology with file storage.

    Like the flagship USS Enterprise NCC-1701-D but using file-based storage
    instead of LMDB. Maintains the reliability and robustness of the original
    with a simpler storage mechanism.

    Features file-based persistent storage, Unix socket communication,
    multiprocessing workers, and proven architectural patterns.

    Perfect for:
    - Production applications with simpler storage needs
    - Distributed processing with file-based state
    - Workloads requiring human-readable state inspection
    - Systems with file-based data requirements

    Registry: NCC-1701-D-F (Galaxy-class with file modifications)
    Captain: Jean-Luc Picard

    Args:
        app_spec: Application spec to deploy
        worker_count: Number of worker processes (default: 4)
        storage_path: Directory path for file storage (default: ".data")
        socket_base: Base path for Unix sockets (default: "/tmp/enterprise_file")
        app_name: Name for the main application (default: "enterprise_file_app")

    Returns:
        Complete application spec ready for deployment
    """

    # 1. Create base state with file persistence
    base_state = get_file_state_spec(path=storage_path, mode="write", name=f"{app_name}_state")

    # 2. Create RPC specs for state service
    state_client, state_server = get_rpyc_specs(
        rpc_type="unix",
        address=f"{socket_base}_state.sock",
        client_name=f"{app_name}_state_client",
        server_name=f"{app_name}_state_server",
    )

    # 3. Create proxied state with launcher capability
    proxied_state = (
        SpecBuilder(base_state)
        .as_proxy(state_client)
        .with_launcher(
            get_launcher_spec(
                host=state_server,
                launcher_type="multiprocessing",
                name=f"{app_name}_state_launcher",
            )
        )
        .build()
    )

    # 4. Create proxy state for workers (without launcher)
    proxy_state_for_workers = SpecBuilder(base_state).as_proxy(state_client).build()

    # 5. Create base worker app spec
    base_worker = app_spec.with_value_at("state", value=proxy_state_for_workers).with_value_at(
        "name", value="worker"
    )

    # 6. Create worker fleet with replication
    worker_client, worker_server = get_rpyc_specs(
        rpc_type="unix",
        address=f"{socket_base}_worker.sock",
        client_name="worker_client",
        server_name="worker_server",
    )

    worker_fleet = (
        SpecBuilder(base_worker)
        .as_proxy(worker_client)
        .with_launcher(
            get_launcher_spec(
                host=worker_server, launcher_type="multiprocessing", name="worker_launcher"
            )
        )
        .replicate(
            count=worker_count,
            paths={
                ("client_spec", "connection", "socket_path"): f"{socket_base}_worker_{{}}.sock",
                ("launcher_spec", "host", "socket_path"): f"{socket_base}_worker_{{}}.sock",
                ("inner_spec", "name"): "worker_{}",
                ("client_spec", "name"): "worker_{}_client",
                ("launcher_spec", "name"): "worker_{}_launcher",
            },
        )
    )

    # 7. Create runtime with worker fleet
    runtime = RuntimeSpec(fleet=tuple(worker_fleet), name=f"{app_name}_runtime")

    # 8. Create main application spec
    main_app = app_spec.with_value_at(
        "state",
        value=proxied_state,
    ).with_value_at(
        "runtime",
        value=runtime,
    )

    return main_app


def get_defiant_topology(app_spec: AppSpec, **kwargs) -> Spec:
    """
    Create a Defiant NX-74205 topology for ultra-low latency applications.

    Like the USS Defiant NX-74205 - small, fast, combat-ready. Stripped down
    for maximum performance with minimal overhead. Benjamin Sisko's warship
    built specifically for fighting the Borg and Dominion.

    Features:
    - Memory-based storage for speed
    - Minimal serialization overhead
    - Optimized worker configurations (2 workers max)
    - Low-latency communication patterns

    Perfect for:
    - High-frequency trading
    - Real-time processing
    - Gaming backends
    - Live data streaming

    Registry: NX-74205 (Defiant-class)
    Captain: Benjamin Sisko
    """
    raise NotImplementedError(
        "Defiant NX-74205 topology coming soon - tough little ship, built for combat"
    )


def get_voyager_topology(app_spec: AppSpec, **kwargs) -> Spec:
    """
    Create a Voyager NCC-74656 topology for long-running exploration workloads.

    Like the USS Voyager NCC-74656 - built for the long haul, self-sufficient,
    adaptive to unknown challenges. Kathryn Janeway's ship that survived
    70,000 light-years in the Delta Quadrant.

    Features:
    - Resilient storage with backup strategies
    - Adaptive worker scaling
    - Enhanced monitoring and recovery
    - Optimized for batch processing
    - Auto-repair capabilities

    Perfect for:
    - Data processing pipelines
    - Long-running analytics
    - ETL workloads
    - Research computing

    Registry: NCC-74656 (Intrepid-class)
    Captain: Kathryn Janeway
    """
    raise NotImplementedError(
        "Voyager NCC-74656 topology coming soon - there's coffee in that nebula"
    )


def get_cerritos_topology(
    app_spec: AppSpec,
    *,
    worker_count: int = 4,
    storage_path: str = ".db",
    app_name: str = "local_app",
) -> Spec:
    """
    Create a Cerritos NCC-75567 topology for simple development work.

    Like the USS Cerritos NCC-75567 - California-class vessel doing the
    important but unglamorous "second contact" work. Perfect for development,
    testing, and utility operations.

    Features:
    - Simple file storage (not for production)
    - State worker runs in the same process
    - Single process with threaded workers
    - Easy to understand and debug

    Perfect for:
    - Development and testing
    - Learning and prototyping

    Registry: NCC-75567 (California-class)
    Captain: Carol Freeman
    """

    # 1. Create base state with file persistence
    state = get_file_state_spec(path=storage_path, mode="write", name=f"{app_name}_state")

    # 2. Create base worker app spec
    base_worker = app_spec.with_value_at("state", value=state).with_value_at("name", value="worker")

    # 3. Create worker fleet with replication
    worker_fleet = SpecBuilder(base_worker).replicate(count=worker_count)

    # 4. Create runtime with worker fleet
    runtime = RuntimeSpec(fleet=tuple(worker_fleet), name=f"{app_name}_runtime")

    # 5. Create main application spec
    main_app = app_spec.with_value_at(
        "state",
        value=state,
    ).with_value_at(
        "runtime",
        value=runtime,
    )

    return main_app
