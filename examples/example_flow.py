"""E2E Demo: everypv with Shapes and Slots."""

from __future__ import annotations

import everypv as e
from everybase import Context
from everybase.abc import Print, Seq
from everyshape import Shape


# --- Shape ---


class AppState(Shape):
    name = e.StrRef.slot()
    age = e.IntRef.slot()


# --- Run ---


async def main():
    from tkv.tkv.storage import StorageProtocol

    from everypv.adapters.codecs import TextCodec as Codec
    from everypv.adapters.storages.textdb import TextStorage as Storage

    with Storage(".db", codec=Codec()) as storage:
        ctx = Context().with_handle(StorageProtocol, storage)

        await e.Atomic(Seq(AppState.name.set("Alice"), AppState.age.set(30))).execute(ctx)
        await e.Atomic(Seq(Print("name", AppState.name), Print("age", AppState.age))).execute(ctx)
        await e.Atomic(
            Seq(AppState.age.set(31), Print("name", AppState.name), Print("age", AppState.age))
        ).execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
