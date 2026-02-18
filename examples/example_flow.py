"""E2E Demo: everypv with Shapes and Slots."""

from __future__ import annotations

import everypv as e
from everybase import Context
from everybase.abc import Print, Seq
from everypv.views import DictView
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
        ctx = Context().with_handle(StorageProtocol, storage, shape=AppState)

        await e.Atomic(
            AppState,
            DictView,
            Seq(
                AppState.name.set("Alice"),
                AppState.age.set(30),
            ),
        ).execute(ctx)

        await e.Atomic(
            AppState,
            DictView,
            Seq(
                Print("name", AppState.name.get()),
                Print("age", AppState.age.get()),
            ),
        ).execute(ctx)

        await e.Atomic(
            AppState,
            DictView,
            Seq(
                AppState.age.set(31),
                Print("name", AppState.name.get()),
                Print("age", AppState.age.get()),
            ),
        ).execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
