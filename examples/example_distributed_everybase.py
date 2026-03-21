#!/usr/bin/env python3
"""
Distributed everybase e2e example.

One spec tree describes everything. Runtime resolves the Attach chain.
Swap the navigator spec for distributed: same flow, same Shape.
"""

import asyncio

from composables import Runtime
from composables.spec import SpecBuilder
from eb_distributed import (
    ContextSpec,
    InMemoryStorageSpec,
    InvisiblesClientSpec,
    NavigatorSpec,
    ProcessLauncherSpec,
)

import eb_virtuals as ebv
from everybase.abc import Print, Seq
from everybase.shape import Shape


# ============================================================================
# Specs
# ============================================================================

nav_spec = NavigatorSpec(
    storage_resource=InMemoryStorageSpec(),
)

# Local
local_ctx_spec = ContextSpec(storage=nav_spec)

# Distributed: navigator in subprocess via invisibles RPC
socket_path = "/tmp/.sock-eb-distributed"  # noqa: S108
distributed_nav_spec = (
    SpecBuilder(nav_spec)
    .as_proxy(InvisiblesClientSpec(transport="unix", address=socket_path))
    .with_launcher(
        ProcessLauncherSpec(
            transport="unix",
            address=socket_path,
        )
    )
    .build()
)
distributed_ctx_spec = ContextSpec(storage=distributed_nav_spec)


# ============================================================================
# Flow - pure everybase, no infra concerns
# ============================================================================


class Data(Shape):
    price = ebv.FloatRef.slot()
    quantity = ebv.IntRef.slot()


flow = Seq(
    Data.price.store(12.4),
    Data.quantity.store(2),
    Print("price", Data.price),
    Print("quantity", Data.quantity),
    Print("total", Data.price * Data.quantity),
)


# ============================================================================
# Main
# ============================================================================


async def main():
    async with Runtime() as runtime:
        # --- Local ---
        print("=== Local ===")
        local_ctx = await runtime.create(local_ctx_spec)
        await ebv.auto_atomic(flow).execute(local_ctx.ctx)

        # --- Distributed: storage in subprocess ---
        print("\n=== Distributed ===")
        distributed_ctx = await runtime.create(distributed_ctx_spec)
        await ebv.auto_atomic(flow).execute(distributed_ctx.ctx)

    print("\nDone. Same flow, same Shape. Local or distributed.")


if __name__ == "__main__":
    asyncio.run(main())
