#!/usr/bin/env python3
"""
Distributed execution e2e example.

Same Calculator resource, two ways:
  1. Local - runtime.create(calc_spec)
  2. Distributed - SpecBuilder(calc_spec).as_proxy(client).with_launcher(launcher).build()

Same interface. Swap the spec.
"""

import asyncio

import attrs
from composables import Resource, ResourceSpec, Runtime
from composables.spec import SpecBuilder

from eb_distributed import InvisiblesClientSpec, ProcessLauncherSpec


# ============================================================================
# Calculator Resource
# ============================================================================


class Calculator(Resource):
    async def setup(self):
        self._history: list[str] = []

    def add(self, a: int, b: int) -> int:
        result = a + b
        self._history.append(f"add({a}, {b}) = {result}")
        return result

    def multiply(self, a: int, b: int) -> int:
        result = a * b
        self._history.append(f"multiply({a}, {b}) = {result}")
        return result

    def get_history(self) -> list[str]:
        return list(self._history)


@attrs.frozen(slots=True, kw_only=True)
class CalculatorSpec(ResourceSpec):
    factory: type = Calculator
    name: str = "calculator"


calc_spec = CalculatorSpec()

distributed_spec = (
    SpecBuilder(calc_spec)
    .as_proxy(
        InvisiblesClientSpec(transport="unix", address="/tmp/.sock-eb-calc"),  # noqa: S108
    )
    .with_launcher(
        ProcessLauncherSpec(
            transport="unix",
            address="/tmp/.sock-eb-calc",  # noqa: S108
        ),
    )
    .build()
)

# ============================================================================
# Main
# ============================================================================


async def main():
    async with Runtime() as runtime:
        # --- Local ---
        print("=== Local ===")
        calc = await runtime.create(calc_spec)
        print(f"  add(2, 3) = {calc.add(2, 3)}")
        print(f"  multiply(4, 5) = {calc.multiply(4, 5)}")
        print(f"  history: {calc.get_history()}")

        # --- Distributed: same spec, wrapped ---
        print("\n=== Distributed (subprocess + invisibles RPC) ===")
        remote = await runtime.create(distributed_spec)
        print(f"  add(10, 20) = {remote.add(10, 20)}")
        print(f"  multiply(6, 7) = {remote.multiply(6, 7)}")
        print(f"  history: {remote.get_history()}")

    print("\nSame interface. Swap the spec.")


if __name__ == "__main__":
    asyncio.run(main())
