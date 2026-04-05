"""End-to-end example: term composition, flows, and Ref-based Type access.

Demonstrates the core everybase concepts without external dependencies:
- Term values and lazy expression composition
- Flow control (Seq, If, ForRange)
- method/prop descriptors on Ref subclasses
- Context-based execution
"""

from __future__ import annotations

import asyncio

from nu_virtuals import ItemRef, auto_atomic
from nu import Arg, Context, Term
from nu.abc import (
    FloatI,
    ForRange,
    If,
    IntI,
    Print,
    Seq,
    TypeBase,
    Interface,
    method,
    prop,
)
from nu.shape import ItemStoreCmd, Shape, Slot


# =============================================================================
# REF + METHOD DESCRIPTORS — context-resolved Type access
# =============================================================================
# A Ref subclass resolves its target from Context at execution time.
# method() and prop() descriptors create term expressions that proxy calls
# through the ref.


class Calculator:
    """Plain Python class we want to expose through the term system."""

    def __init__(self, precision: int = 2) -> None:
        self.precision = precision

    def add(self, a: float, b: float) -> float:
        return round(a + b, self.precision)

    def multiply(self, a: float, b: float) -> float:
        return round(a * b, self.precision)


class CalculatorType(TypeBase):
    """Calculator typed interfaces - Type.

    method() descriptors declare what the underlying object can do.
    Class-level access (CalculatorRef.add(...)) creates lazy term
    expressions that resolve the Calculator at execution time.
    """

    add = method(FloatI, "add")
    multiply = method(FloatI, "multiply")
    precision = prop(IntI, "precision")


class CalculatorValue(CalculatorType, Interface):
    """Computed Value"""


class CalculatorRef(ItemRef[Calculator, CalculatorValue], CalculatorType):
    """Ref that resolves a Calculator from context."""

    def __init__(
        self,
        address: object,
        parent: object,
        owner_shape: type | None = None,
    ) -> None:
        super().__init__(address, Calculator, CalculatorValue, parent, owner_shape)

    @classmethod
    def slot(cls) -> CalculatorRef:
        """Create a slot for Fraction values."""
        return Slot(cls)  # type: ignore[return-value]

    def store(self, value: Arg[Calculator]) -> CalculatorValue:
        """Store the Calculator value."""
        if isinstance(value, Calculator):
            val = CalculatorValue(value)
        elif isinstance(value, Term):
            val = value
        return CalculatorValue(ItemStoreCmd(self, val))


# =============================================================================
# Shapes
# =============================================================================
# Structures for data


class Services(Shape):
    calc = CalculatorRef.slot()


# =============================================================================
# TERM VALUES — lazy composition
# =============================================================================
# Values compose into expression trees. Nothing executes until .execute(ctx).

price = FloatI(99.95)
quantity = IntI(3)
tax_rate = FloatI(0.08)

subtotal = price * quantity  # FloatI(MulOp(...))
tax = subtotal * tax_rate
total = subtotal + tax

is_expensive = total > 250


# =============================================================================
# FLOWS — structured execution
# =============================================================================
# Flows are also terms. They compose and execute the same way.

checkout_flow = Seq(
    Print("subtotal", subtotal),
    Print("tax", tax),
    Print("total", total),
    If(is_expensive, Print(">> expensive order!"), Print(">> regular order")),
)

tick_flow = ForRange(IntI(0), IntI(3), Print("tick!"))


# =============================================================================
# 4. PUTTING IT ALL TOGETHER
# =============================================================================


async def main() -> None:
    from virtuals.tkv.storage import StorageProtocol

    from nu_virtuals.presets import memory_storage, rocksdb_storage_inmemory

    with rocksdb_storage_inmemory(".db-e2e-test") as rocksdb:
        with memory_storage() as memdb:
            ctx = Context()

            ctx = ctx.bind(rocksdb, StorageProtocol)
            ctx = ctx.bind(memdb, StorageProtocol, Services)  # sharded: Services on memdb

            # --- Compose ref methods into flows ---
            print("=== Ref Methods in Flows ===")
            calc_flow = Seq(
                Services.calc.store(Calculator(4)),
                Print("add", Services.calc.add(FloatI(1.0), FloatI(2.0))),
                Print("mul", Services.calc.multiply(FloatI(3.0), FloatI(4.0))),
                If(
                    Services.calc.add(FloatI(100.0), FloatI(200.0)) > 250,
                    Print(">> big sum!"),
                    Print(">> small sum"),
                ),
            )
            calc_flow = auto_atomic(calc_flow, scope=Services)
            await calc_flow.execute(ctx)


if __name__ == "__main__":
    asyncio.run(main())


# # --- Pure term expressions ---
# print("=== Term Expressions ===")
# print(f"subtotal = {await subtotal.execute(ctx)}")
# print(f"tax      = {await tax.execute(ctx)}")
# print(f"total    = {await total.execute(ctx)}")
# print(f"expensive? {await is_expensive.execute(ctx)}")
# print()

# # --- Flows ---
# print("=== Flows ===")
# await checkout_flow.execute(ctx)
# print()
# await tick_flow.execute(ctx)
# print()

# # --- Ref-based class access ---
# print("=== Ref-based Class Access ===")
# ctx_with_calc = ctx.bind(Calculator(precision=2), Calculator)

# # Class-level access creates context-resolved expressions
# result = await CalculatorRef.add(FloatI(10.5), FloatI(20.3)).execute(
#     ctx_with_calc
# )
# print(f"CalculatorRef.add(10.5, 20.3) = {result}")

# result = await CalculatorRef.multiply(FloatI(7.0), FloatI(6.0)).execute(
#     ctx_with_calc
# )
# print(f"CalculatorRef.multiply(7.0, 6.0) = {result}")

# prec = await CalculatorRef.precision.execute(ctx_with_calc)
# print(f"CalculatorRef.precision = {prec}")
# print()
