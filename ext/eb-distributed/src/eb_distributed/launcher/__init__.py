"""Launcher - @ray.remote actors that host composables Resources."""

from .process import RayProcess, WorkerProcess


__all__ = [
    "RayProcess",
    "WorkerProcess",
]
