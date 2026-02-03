"""Example: standard library types across substrates.

Shows Decimal, datetime, Path, UUID, and Percentage refs used
together in a dict-substrate Shape — then cross-type operations.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from every_dict import (
    DictDatetimeRef,
    DictDecimalRef,
    DictPathRef,
    DictPercentageRef,
    DictTimedeltaRef,
    DictUUIDRef,
    IntRef,
    Shape,
)
from everybase import Context


# =============================================
# Shape mixing several stdtype refs
# =============================================


class Invoice(Shape):
    number = IntRef.slot()
    id = DictUUIDRef.slot()
    amount = DictDecimalRef.slot()
    tax_rate = DictPercentageRef.slot()
    created_at = DictDatetimeRef.slot()
    due_in = DictTimedeltaRef.slot()
    receipt_path = DictPathRef.slot()


# =============================================
# Run
# =============================================


async def main():
    data: dict = {}
    ctx = Context().with_handle(dict, data, shape=Invoice)

    # -- write fields --
    await Invoice.number.set(1042).execute(ctx)
    await Invoice.id.set("550e8400-e29b-41d4-a716-446655440000").execute(ctx)
    await Invoice.amount.set(Decimal("1499.99")).execute(ctx)
    await Invoice.tax_rate.set(8.25).execute(ctx)
    await Invoice.created_at.set(datetime(2025, 6, 15, 14, 30)).execute(ctx)
    await Invoice.due_in.set(timedelta(days=30)).execute(ctx)
    await Invoice.receipt_path.set(Path("/invoices/2025/1042.pdf")).execute(ctx)

    print("Raw dict:", data)

    # -- read back with typed operations --
    amt = await Invoice.amount.get().execute(ctx)
    print(f"Amount: {amt}")

    tax = await Invoice.tax_rate.get().execute(ctx)
    print(f"Tax rate: {tax}")

    # arithmetic on Decimal values
    total = await (Invoice.amount.get() * Decimal("1.0825")).execute(ctx)
    print(f"Total with tax: {total}")

    # datetime operations
    created = await Invoice.created_at.get().execute(ctx)
    print(f"Created: {created.isoformat()}")

    # timedelta
    due = await Invoice.due_in.get().execute(ctx)
    print(f"Due in: {due.days} days")

    # path operations
    receipt = await Invoice.receipt_path.get().execute(ctx)
    print(f"Receipt: {receipt}")
    print(f"  stem: {await Invoice.receipt_path.get().stem().execute(ctx)}")
    print(f"  suffix: {await Invoice.receipt_path.get().suffix().execute(ctx)}")
    print(f"  parent: {await Invoice.receipt_path.get().parent().execute(ctx)}")

    # UUID
    uid = await Invoice.id.get().execute(ctx)
    print(f"UUID: {uid}")
    print(f"  version: {await Invoice.id.get().version().execute(ctx)}")

    # cross-type: compute due date from created_at + due_in
    due_date = await (Invoice.created_at.get() + Invoice.due_in.get()).execute(ctx)
    print(f"Due date: {due_date.isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
