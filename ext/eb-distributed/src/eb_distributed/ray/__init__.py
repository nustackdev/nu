"""Ray integration - distributed execution via Ray actors.

Modules:
    process.py   - @ray.remote actors (RayProcess, WorkerProcess)
    resource.py  - composables Resources (RayActor, RayWorker + Specs)
    presets.py   - topology preset (distributed)

Usage:
    # Service: Navigator + InvisiblesServer on a Ray node
    service = await runtime.create(RayActorSpec(
        inner_spec=InvisiblesServerSpec(...),
    ))

    # Worker: everybase tree executor on a Ray node
    worker = await runtime.create(RayWorkerSpec(
        inner_spec=WorkerSpec(context=ContextSpec(storage=nav_proxy)),
    ))
    ctx = ctx.bind(worker, Worker, 0)
"""

from .resource import RayActor, RayActorSpec, RayWorker, RayWorkerSpec


__all__ = [
    "RayActor",
    "RayActorSpec",
    "RayWorker",
    "RayWorkerSpec",
]
