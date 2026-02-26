"""E2E Example."""

from __future__ import annotations

from datetime import datetime

import everybase.abc as f
import everypv as pv
from everyshape import Shape


class AppState(Shape):
    name = pv.StrRef.slot()
    age = pv.IntRef.slot()
    online = pv.DatetimeRef.slot()


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
    from tkv.tkv.storage import StorageProtocol

    from everybase import Context
    from everypv.adapters.storage import text_storage

    with text_storage(".db") as storage:
        ctx = Context().bind(storage, StorageProtocol)
        for demo in demos:
            tree = pv.auto_atomic(demo)
            await tree.execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
