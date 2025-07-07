# """
# Worker endpoint representation for resource pools.

# A worker is simply a Loomi server running at a specific endpoint.
# This module provides minimal abstractions for tracking these endpoints.
# """

# from __future__ import annotations

# from dataclasses import dataclass
# from typing import Any, Dict, List

# __all__ = [
#     "WorkerEndpoint",
#     "generate_endpoints",
# ]


# @dataclass(frozen=True)
# class WorkerEndpoint:  # Should be replaced with Spec. endopint is misleading
#     """
#     Represents an endpoint where a Loomi server is running.

#     This is a minimal representation - the actual "worker" is the
#     Loomi server service running at this endpoint, managed by adapters.
#     """

#     # Unique identifier for this worker endpoint
#     worker_id: str

#     # Index in the pool (0, 1, 2, ...)
#     worker_index: int

#     # Protocol type ("tcp", "unix", "http", etc.)
#     protocol: str

#     # Address where the Loomi server can be reached
#     address: str

#     # Additional metadata for load balancing or debugging
#     metadata: Dict[str, Any] | None = None

#     def __post_init__(self):
#         if self.metadata is None:
#             object.__setattr__(self, "metadata", {})


# def generate_endpoints(
#     protocol: str, worker_count: int, base_config: Dict[str, Any]
# ) -> List[WorkerEndpoint]:
#     """
#     Generate worker endpoints for a given protocol and configuration.

#     Args:
#         protocol: Protocol type ("tcp", "unix", etc.)
#         worker_count: Number of worker endpoints to generate
#         base_config: Protocol-specific base configuration

#     Returns:
#         List of WorkerEndpoint instances

#     Examples:
#         >>> # TCP endpoints
#         >>> endpoints = generate_endpoints("tcp", 3, {"base_port": 9000, "host": "localhost"})
#         >>> # Results in endpoints at localhost:9000, localhost:9001, localhost:9002

#         >>> # Unix socket endpoints
#         >>> endpoints = generate_endpoints("unix", 2, {"socket_path_base": "/tmp/worker"})
#         >>> # Results in endpoints at /tmp/worker_0.sock, /tmp/worker_1.sock
#     """
#     endpoints = []

#     for i in range(worker_count):
#         worker_id = f"worker_{i}"

#         if protocol == "tcp":
#             host = base_config.get("host", "localhost")
#             base_port = base_config.get("base_port", 9000)
#             port = base_port + i
#             address = f"{host}:{port}"

#         elif protocol == "unix":
#             socket_path_base = base_config.get("socket_path_base", "/tmp/loomi_worker")
#             address = f"{socket_path_base}_{i}.sock"

#         elif protocol == "http":
#             host = base_config.get("host", "localhost")
#             base_port = base_config.get("base_port", 8000)
#             port = base_port + i
#             address = f"http://{host}:{port}"

#         else:
#             raise ValueError(f"Unsupported protocol: {protocol}")

#         endpoint = WorkerEndpoint(
#             worker_id=worker_id,
#             worker_index=i,
#             protocol=protocol,
#             address=address,
#             metadata={"created_from": base_config},
#         )

#         endpoints.append(endpoint)

#     return endpoints
