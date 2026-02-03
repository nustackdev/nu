"""E2E Demo: every_pv with Shapes and Slots."""

from __future__ import annotations

import every_pv as e
from every_flow import Print, Seq
from every_pv.views import DictView
from everybase import Context


# --- Shape ---


class AppState(e.Shape):
    name = e.StrRef.slot()
    age = e.IntRef.slot()


# --- Run ---


async def main():
    from tkv.tkv.storage import StorageProtocol

    from every_pv.adapters.codecs import TextCodec as Codec
    from every_pv.adapters.storages.textdb import TextStorage as Storage

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
