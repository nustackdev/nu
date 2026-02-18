"""End-to-end example: term composition, flows, and Ref-based Type access.

Demonstrates the core everybase concepts without external dependencies:
- Term values and lazy expression composition
- Flow control (Seq, If, ForRange)
- method/prop descriptors on Ref subclasses
- Context-based execution
"""

from __future__ import annotations

import asyncio

from everybase import Context
from everybase.abc import (
    FloatValue,
    IntValue,
    method,
    prop,
)
from everybase.abc.flows import ForRange, If, Print, Seq
from everybase.core import Ref


# =============================================================================
# 1. TERM VALUES — lazy composition
# =============================================================================
# Values compose into expression trees. Nothing executes until .execute(ctx).

price = FloatValue(99.95)
quantity = IntValue(3)
tax_rate = FloatValue(0.08)

subtotal = price * quantity  # FloatValue(MulOp(...))
tax = subtotal * tax_rate
total = subtotal + tax

is_expensive = total > 250


# =============================================================================
# 2. FLOWS — structured execution
# =============================================================================
# Flows are also terms. They compose and execute the same way.

checkout_flow = Seq(
    Print("subtotal", subtotal),
    Print("tax", tax),
    Print("total", total),
    If(is_expensive, Print(">> expensive order!"), Print(">> regular order")),
)

tick_flow = ForRange(IntValue(0), IntValue(3), Print("tick!"))


# =============================================================================
# 3. REF + METHOD DESCRIPTORS — context-resolved Type access
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


class CalculatorRef(Ref[Calculator]):
    """Ref that resolves a Calculator from context.

    method() descriptors declare what the underlying object can do.
    Class-level access (CalculatorRef.add(...)) creates lazy term
    expressions that resolve the Calculator at execution time.
    """

    add = method(FloatValue, "add")
    multiply = method(FloatValue, "multiply")
    precision = prop(IntValue, "precision")

    async def resolve(self, ctx: Context) -> str:
        return "calculator"

    async def fetch(self, ctx: Context) -> Calculator:
        return ctx.get(Calculator)


# =============================================================================
# 4. PUTTING IT ALL TOGETHER
# =============================================================================


async def main() -> None:
    ctx = Context()

    # --- Pure term expressions ---
    print("=== Term Expressions ===")
    print(f"subtotal = {await subtotal.execute(ctx)}")
    print(f"tax      = {await tax.execute(ctx)}")
    print(f"total    = {await total.execute(ctx)}")
    print(f"expensive? {await is_expensive.execute(ctx)}")
    print()

    # --- Flows ---
    print("=== Flows ===")
    await checkout_flow.execute(ctx)
    print()
    await tick_flow.execute(ctx)
    print()

    # --- Ref-based class access ---
    print("=== Ref-based Class Access ===")
    ctx_with_calc = ctx.with_handle(Calculator, Calculator(precision=2))

    # Class-level access creates context-resolved expressions
    result = await CalculatorRef.add(FloatValue(10.5), FloatValue(20.3)).execute(ctx_with_calc)
    print(f"CalculatorRef.add(10.5, 20.3) = {result}")

    result = await CalculatorRef.multiply(FloatValue(7.0), FloatValue(6.0)).execute(ctx_with_calc)
    print(f"CalculatorRef.multiply(7.0, 6.0) = {result}")

    prec = await CalculatorRef.precision.execute(ctx_with_calc)
    print(f"CalculatorRef.precision = {prec}")
    print()

    # --- Compose ref methods into flows ---
    print("=== Ref Methods in Flows ===")
    calc_flow = Seq(
        Print("add", CalculatorRef.add(FloatValue(1.0), FloatValue(2.0))),
        Print("mul", CalculatorRef.multiply(FloatValue(3.0), FloatValue(4.0))),
        If(
            CalculatorRef.add(FloatValue(100.0), FloatValue(200.0)) > 250,
            Print(">> big sum!"),
            Print(">> small sum"),
        ),
    )
    await calc_flow.execute(ctx_with_calc)


if __name__ == "__main__":
    asyncio.run(main())
