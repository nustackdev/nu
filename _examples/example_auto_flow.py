"""E2E Example."""

from __future__ import annotations

import every_flow as f
import every_pv as e


class AppState(e.Shape):
    name = e.StrRef.slot()
    age = e.IntRef.slot()


demos = [
    f.Seq(
        AppState.name.set("Alice"),
        AppState.age.set(30),
    ),
    f.Seq(
        f.Print("name", AppState.name.get()),
        f.Print("age", AppState.age.get()),
    ),
    f.Seq(
        AppState.age.set(31),
        f.Print("name", AppState.name.get()),
        f.Print("age", AppState.age.get()),
    ),
]

# --- Run ---


async def main():
    from tkv.tkv.storage import StorageProtocol

    from every_pv.adapters.codecs import TextCodec as Codec
    from every_pv.adapters.storages.textdb import TextStorage as Storage
    from every_pv.views import DictView
    from everybase import Context

    with Storage(".db", codec=Codec()) as storage:
        ctx = Context().with_handle(StorageProtocol, storage, shape=AppState)
        for i in range(len(demos)):
            # Get the tree
            tree = demos[i]
            # Add atomicity
            tree = e.auto_atomic(tree, AppState, DictView)
            # Add other features
            ...
            # Execute the tree
            await tree.execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
