"""Basic Nu example - addition of numbers.

Shows the core pattern: build a tree, then evaluate it.
"""

import asyncio

from nu import BinaryCalc, Context, Value, print_tree


# A leaf Nu that holds a number
class Num(Value[float | int]):
    pass


# A pure binary op: addition
class Add(BinaryCalc[float | int]):
    def apply(self, left: float | int, right: float | int) -> float | int:
        return left + right


# A pure binary op: multiplication
class Mul(BinaryCalc[float | int]):
    def apply(self, left: float | int, right: float | int) -> float | int:
        return left * right


async def main():
    # Build the tree: (3 + 4) * 2
    tree = Mul(
        Add(
            Num(3),
            Num(4),
        ),
        Num(2),
    )

    # Inspect it
    print("Tree:")
    print_tree(tree)

    # Evaluate it
    ctx = Context()
    result = await tree.execute(ctx)
    print(f"\nResult: {result}")

    # Purity check
    print(f"Pure: {tree.is_subtree_pure}")


asyncio.run(main())
