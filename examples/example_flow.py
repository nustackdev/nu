"""E2E Demo: everypv with Shapes and Slots."""

from __future__ import annotations

import eb_pv as e
from everybase import Context
from everybase.abc import Print, Seq
from everybase.shape import Shape


# --- Shape ---


class AppState(Shape):
    name = e.StrRef.slot()
    age = e.IntRef.slot()


# --- Run ---


async def main():
    from virtuals.tkv.tkv.storage import StorageProtocol

    from eb_pv.adapters.storage import text_storage

    with text_storage(".db") as storage:
        ctx = Context().bind(storage, StorageProtocol)

        await e.Atomic(Seq(AppState.name.set("Alice"), AppState.age.set(30))).execute(ctx)
        await e.Atomic(Seq(Print("name", AppState.name), Print("age", AppState.age))).execute(ctx)
        await e.Atomic(
            Seq(AppState.age.set(31), Print("name", AppState.name), Print("age", AppState.age))
        ).execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
