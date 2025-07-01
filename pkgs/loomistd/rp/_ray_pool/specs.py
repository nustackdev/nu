from __future__ import annotations

from typing import Any

from loomi.spec import Spec, SpecField

__all__ = [
    "RayWorkerPoolSpec",
]
from .pool import RayWorkerPool


class RayWorkerPoolSpec(Spec):
    """Specification for Ray worker pool."""

    name: str = SpecField(default="ray_worker_pool")
    factory: type = SpecField(default=RayWorkerPool)

    # Ray configuration
    max_workers: int = SpecField(default=4)
    ray_address: str | None = SpecField(default=None)  # None for local cluster
    ray_init_kwargs: dict[str, Any] = SpecField(default_factory=dict)
    shutdown_ray_on_disconnect: bool = SpecField(default=False)

    # Connection configuration
    worker_server_specs: list[Spec] = SpecField()
    worker_client_specs: list[Spec] = SpecField()


# class WorkerTCPServerSpec(Spec):
#     """Specification for TCP-based RPyC worker server."""

#     name: str = SpecField(default="worker_rpyc_tcp_server")
#     factory: type = SpecField(default=RPyCTCPServer)

#     # Server configuration
#     bind_address: str = SpecField(default="localhost")
#     bind_port: int = SpecField(...)  # Must be specified per worker
#     auto_register: bool = SpecField(default=False)

#     # Connection configuration
#     config: dict = SpecField(default_factory=dict)

#     @classmethod
#     def for_worker(
#         cls, worker_index: int, base_port: int = 18812, **kwargs
#     ) -> "WorkerTCPServerSpec":
#         """Create a TCP server spec for a specific worker."""
#         return cls(
#             worker_id=f"worker_{worker_index}",
#             worker_index=worker_index,
#             bind_port=base_port + worker_index,
#             **kwargs,
#         )


# class WorkerUnixServerSpec(Spec):
#     """Specification for Unix socket-based RPyC worker server."""

#     name: str = SpecField(default="worker_rpyc_unix_server")
#     factory: type = SpecField(default=RPyCUnixServer)

#     # Server configuration
#     socket_path: str = SpecField(...)  # Must be specified per worker
#     auto_register: bool = SpecField(default=False)

#     @classmethod
#     def for_worker(
#         cls, worker_index: int, socket_base: str = "/tmp/loomi_worker", **kwargs
#     ) -> "WorkerUnixServerSpec":
#         """Create a Unix server spec for a specific worker."""
#         return cls(
#             worker_id=f"worker_{worker_index}",
#             worker_index=worker_index,
#             socket_path=f"{socket_base}_{worker_index}.sock",
#             **kwargs,
#         )


# def generate_worker_specs(
#     server_type: str, worker_count: int, base_config: dict
# ) -> List[WorkerTCPServerSpec | WorkerUnixServerSpec]:
#     """
#     Generate worker server specs for a given server type and configuration.

#     Args:
#         server_type: Type of server ("tcp" or "unix")
#         worker_count: Number of worker specs to generate
#         base_config: Base configuration for the server type

#     Returns:
#         List of worker server specs

#     Examples:
#         >>> # TCP worker specs
#         >>> specs = generate_worker_specs("tcp", 3, {"base_port": 9000, "bind_address": "localhost"})
#         >>> # Results in specs for ports 9000, 9001, 9002

#         >>> # Unix socket worker specs
#         >>> specs = generate_worker_specs("unix", 2, {"socket_base": "/tmp/worker"})
#         >>> # Results in specs for /tmp/worker_0.sock, /tmp/worker_1.sock
#     """
#     specs = []

#     if server_type == "tcp":
#         base_port = base_config.get("base_port", 18812)
#         bind_address = base_config.get("bind_address", "localhost")

#         for i in range(worker_count):
#             spec = WorkerTCPServerSpec.for_worker(
#                 worker_index=i,
#                 base_port=base_port,
#                 bind_address=bind_address,
#                 **{k: v for k, v in base_config.items() if k not in ["base_port", "bind_address"]},
#             )
#             specs.append(spec)

#     elif server_type == "unix":
#         socket_base = base_config.get("socket_base", "/tmp/loomi_worker")

#         for i in range(worker_count):
#             spec = WorkerUnixServerSpec.for_worker(
#                 worker_index=i,
#                 socket_base=socket_base,
#                 **{k: v for k, v in base_config.items() if k not in ["socket_base"]},
#             )
#             specs.append(spec)

#     else:
#         raise ValueError(f"Unsupported server type: {server_type}")

#     return specs
