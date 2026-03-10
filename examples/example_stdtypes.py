"""Example: standard library types with PV substrate.

Shows Decimal, datetime, Path, UUID, and Percentage refs used
together in a PV-substrate Shape — then cross-type operations.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import eb_virtuals as ebv
from everybase import Context
from everybase.shape import Shape


# =============================================
# Shape mixing several stdtype refs
# =============================================


class Invoice(Shape):
    number = ebv.IntRef.slot()
    id = ebv.UUIDRef.slot()
    amount = ebv.DecimalRef.slot()
    tax_rate = ebv.FloatRef.slot()
    created_at = ebv.DatetimeRef.slot()
    due_in = ebv.TimedeltaRef.slot()
    receipt_path = ebv.PathRef.slot()


# =============================================
# Run
# =============================================


async def main():
    from virtuals import View
    from virtuals.codecs import TextCodec as Codec
    from virtuals.views import DictView

    from eb_virtuals.presetss.textdb import TextStorage as Storage

    with Storage(".db-stdtypes", codec=Codec()) as storage:
        with storage.transaction() as tx:
            root = DictView.open_root(tx)
            ctx = Context().bind(root, View, Invoice)

            # -- write fields --
            await Invoice.number.store(1042).execute(ctx)
            await Invoice.id.store("550e8400-e29b-41d4-a716-446655440000").execute(ctx)
            await Invoice.amount.store(Decimal("1499.99")).execute(ctx)
            await Invoice.tax_rate.store(8.25).execute(ctx)
            await Invoice.created_at.store(datetime(2025, 6, 15, 14, 30)).execute(ctx)
            await Invoice.due_in.store(timedelta(days=30)).execute(ctx)
            await Invoice.receipt_path.store(Path("/invoices/2025/1042.pdf")).execute(ctx)

            # -- read back --
            amt = await Invoice.amount.execute(ctx)
            print(f"Amount: {amt}")

            tax = await Invoice.tax_rate.execute(ctx)
            print(f"Tax rate: {tax}")

            created = await Invoice.created_at.execute(ctx)
            print(f"Created: {created}")

            due = await Invoice.due_in.execute(ctx)
            print(f"Due in: {due}")

            receipt = await Invoice.receipt_path.execute(ctx)
            print(f"Receipt: {receipt}")

            uid = await Invoice.id.execute(ctx)
            print(f"UUID: {uid}")


if __name__ == "__main__":
    asyncio.run(main())
