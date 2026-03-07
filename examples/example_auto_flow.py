"""E2E Example."""

from __future__ import annotations

from datetime import datetime

import eb_virtuals as ebv
import everybase.abc as f
from everybase.shape import Shape


class AppState(Shape):
    name = ebv.StrRef.slot()
    age = ebv.IntRef.slot()
    online = ebv.DatetimeRef.slot()


demos = [
    f.Seq(
        AppState.name.set("Alice"),
        AppState.age.set(30),
        AppState.online.set(datetime.now()),
    ),
    f.Seq(
        f.Print("name", AppState.name),
        f.Print("age", AppState.age),
        f.Print("online", AppState.online),
    ),
]

# --- Run ---


async def main():
    from virtuals.tkv.storage import StorageProtocol

    from eb_virtuals.presets import text_storage
    from everybase import Context

    with text_storage(".db") as storage:
        ctx = Context().bind(storage, StorageProtocol)
        for demo in demos:
            tree = ebv.auto_atomic(demo)
            await tree.execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
