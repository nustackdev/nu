"""E2E Demo: eb_virtuals with Shapes and Slots."""

from __future__ import annotations

import eb_virtuals as ebv
from everybase import Context
from everybase.abc import Print, Seq
from everybase.shape import Shape


# --- Shape ---


class AppState(Shape):
    name = ebv.StrRef.slot()
    age = ebv.IntRef.slot()


# --- Run ---


async def main():
    from virtuals.tkv import StorageProtocol

    from eb_virtuals.presets import text_storage

    with text_storage(".db") as storage:
        ctx = Context().bind(storage, StorageProtocol)

        await ebv.Atomic(Seq(AppState.name.store("Alice"), AppState.age.store(30))).execute(ctx)
        await ebv.Atomic(Seq(Print("name", AppState.name), Print("age", AppState.age))).execute(ctx)
        await ebv.Atomic(
            Seq(AppState.age.store(31), Print("name", AppState.name), Print("age", AppState.age))
        ).execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
