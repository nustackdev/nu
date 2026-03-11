"""Lazy dict composition — set values, then read with complex term expressions."""

from __future__ import annotations

import eb_virtuals as ebv
from everybase import Context
from everybase.abc import Print, Seq, fn
from everybase.shape import Shape


class Portfolio(Shape):
    name = ebv.StrRef.slot()
    assets = ebv.DictRef.slot(value_type=float)
    tags = ebv.ListRef.slot(item_type=str)


async def main():
    from virtuals.tkv import StorageProtocol

    from eb_virtuals.presets import memory_storage

    with memory_storage() as storage:
        ctx = Context().bind(storage, StorageProtocol)

        await ebv.Atomic(
            Seq(
                # populate
                Portfolio.name.store("Growth Fund"),
                Portfolio.assets["AAPL"].store(150.0),
                Portfolio.assets["GOOGL"].store(2800.0),
                Portfolio.assets["MSFT"].store(420.5),
                Portfolio.assets["AMZN"].store(185.0),
                Portfolio.tags.store(["tech", "growth", "us-large-cap"]),
                # lazy reads — nothing touches storage until execute()
                Print("name", Portfolio.name),
                Print("AAPL", Portfolio.assets["AAPL"]),
                Print("keys", Portfolio.assets.keys().to_list()),
                Print("first 2 keys", fn.Take(Portfolio.assets.keys(), 2).to_list()),
                Print("sorted keys", fn.Sorted(Portfolio.assets.keys())),
                Print("has GOOGL?", fn.Contains(Portfolio.assets.keys(), "GOOGL")),
                Print("num assets", fn.Len(Portfolio.assets.keys())),
                Print("tag count", fn.Len(Portfolio.tags)),
                Print("first tag", Portfolio.tags.first()),
                Print("tags[:2]", fn.Take(Portfolio.tags, 2).to_list()),
            )
        ).execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
