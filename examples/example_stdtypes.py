"""Example: standard library types with PV substrate.

Shows Decimal, datetime, Path, UUID, and Percentage refs used
together in a PV-substrate Shape — then cross-type operations.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import everypv as pv
from everybase import Context
from everyshape import Shape


# =============================================
# Shape mixing several stdtype refs
# =============================================


class Invoice(Shape):
    number = pv.IntRef.slot()
    id = pv.UUIDRef.slot()
    amount = pv.DecimalRef.slot()
    tax_rate = pv.FloatRef.slot()
    created_at = pv.DatetimeRef.slot()
    due_in = pv.TimedeltaRef.slot()
    receipt_path = pv.PathRef.slot()


# =============================================
# Run
# =============================================


async def main():
    from pv import View

    from everypv.adapters.codecs import TextCodec as Codec
    from everypv.adapters.storages.textdb import TextStorage as Storage
    from everypv.views import DictView

    with Storage(".db-stdtypes", codec=Codec()) as storage:
        with storage.transaction() as tx:
            root = DictView.open_root(tx)
            ctx = Context().with_handle(View, root, Invoice)

            # -- write fields --
            await Invoice.number.set(1042).execute(ctx)
            await Invoice.id.set("550e8400-e29b-41d4-a716-446655440000").execute(ctx)
            await Invoice.amount.set(Decimal("1499.99")).execute(ctx)
            await Invoice.tax_rate.set(8.25).execute(ctx)
            await Invoice.created_at.set(datetime(2025, 6, 15, 14, 30)).execute(ctx)
            await Invoice.due_in.set(timedelta(days=30)).execute(ctx)
            await Invoice.receipt_path.set(Path("/invoices/2025/1042.pdf")).execute(ctx)

            # -- read back --
            amt = await Invoice.amount.get().execute(ctx)
            print(f"Amount: {amt}")

            tax = await Invoice.tax_rate.get().execute(ctx)
            print(f"Tax rate: {tax}")

            created = await Invoice.created_at.get().execute(ctx)
            print(f"Created: {created}")

            due = await Invoice.due_in.get().execute(ctx)
            print(f"Due in: {due}")

            receipt = await Invoice.receipt_path.get().execute(ctx)
            print(f"Receipt: {receipt}")

            uid = await Invoice.id.get().execute(ctx)
            print(f"UUID: {uid}")


if __name__ == "__main__":
    asyncio.run(main())
