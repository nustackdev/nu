"""E2E Demo: eb_pv with Shapes and Slots."""

from __future__ import annotations

import eb_pv as e
from eb_flow import Print, Seq
from eb_pv.views import DictView
from eb_shape import Shape
from everybase import Context


# --- Shape ---


class AppState(Shape):
    name = e.StrRef.slot()
    age = e.IntRef.slot()


# --- Run ---


async def main():
    from tkv.tkv.storage import StorageProtocol

    from eb_pv.adapters.codecs import TextCodec as Codec
    from eb_pv.adapters.storages.textdb import TextStorage as Storage

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
