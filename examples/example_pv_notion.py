"""PV storage + Notion sync: track local metrics, push user scores to Notion."""

from __future__ import annotations

from datetime import datetime

import every
import every_pv
import every_view
from every_adapters.codecs import BinaryCodec
from every_adapters.storages.inmemdb import InMemoryStorage
from every_notion import EmailSlot, NotionContext, NotionTable, TitleSlot


API_KEY = "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"
DATABASE_ID = "2ed7cf006d4f8025828cd4f3bd373e82"


class Trade(every.Shape):
    symbol = every_pv.slots.StrSlot()
    price = every_pv.slots.FloatSlot()
    qty = every_pv.slots.IntSlot()


class Portfolio(every.Shape):
    trades = every_pv.slots.ShapesListSlot(Trade)
    total_pnl = every_pv.slots.FloatSlot()


class Users(NotionTable):
    database_id = DATABASE_ID
    name = TitleSlot()
    email = EmailSlot()


def run_trading_session(ctx: every_pv.KVContext) -> dict:
    Portfolio.total_pnl.set(0.0).execute(ctx)

    trades = [
        {"symbol": "AAPL", "price": 150.0, "qty": 100},
        {"symbol": "GOOGL", "price": 2800.0, "qty": 10},
        {"symbol": "AAPL", "price": 155.0, "qty": -50},
        {"symbol": "GOOGL", "price": 2850.0, "qty": -10},
    ]
    for t in trades:
        Portfolio.trades.append(t).execute(ctx)

    pnl = (155.0 - 150.0) * 50 + (2850.0 - 2800.0) * 10
    Portfolio.total_pnl.set(pnl).execute(ctx)

    print(f"PnL: ${Portfolio.total_pnl.get().execute(ctx):,.2f}")
    print(f"Trades: {len(trades)}")

    return {"pnl": pnl, "num_trades": len(trades)}


def sync_to_notion(ctx: NotionContext, metrics: dict) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    Users.add_row(
        name=f"Bot {ts} | PnL: ${metrics['pnl']:.0f}",
        email="bot@example.com",
    ).execute(ctx)
    print(f"Synced to Notion: Bot {ts}")


def main() -> None:
    with InMemoryStorage(codec=BinaryCodec()) as storage, storage.transaction() as tx:
        root = every_view.DictView.open_root(tx)
        pv_ctx = every_pv.KVContext.create(root_view=root, storage_context=tx)

        print("=== PV Trading Session ===")
        metrics = run_trading_session(pv_ctx)

        print("\n=== Notion Sync ===")
        with NotionContext.create(api_key=API_KEY) as notion_ctx:
            sync_to_notion(notion_ctx, metrics)


if __name__ == "__main__":
    main()
