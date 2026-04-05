"""Basic Interface example - typed tree construction.

Shows the Interface pattern: wrap literals, chain operations, execute.
Interfaces are construction-time sugar that produce Nu trees.
"""

import asyncio

from nu import BoolI, Context, FloatI, IntI, StrI, print_tree


async def main():
    ctx = Context()

    # --- Arithmetic ---
    x = IntI(5)
    y = IntI(3)
    expr = (x + y) * 2
    print("Tree: (5 + 3) * 2")
    print_tree(expr)
    print(f"= {await expr.execute(ctx)}\n")

    # --- Int/float promotion ---
    half = IntI(10) / 3
    print(f"10 / 3 = {await half.execute(ctx)}")
    print(f"  type: {type(half).__name__}\n")  # FloatI

    # --- Chained arithmetic ---
    chain = ((IntI(100) - 20) * 3 + 7) % 11
    print(f"((100 - 20) * 3 + 7) % 11 = {await chain.execute(ctx)}\n")

    # --- Strings ---
    greeting = StrI("hello") + " " + StrI("world")
    print(f"'hello' + ' ' + 'world' = {await greeting.execute(ctx)}")

    loud = StrI("whisper").upper()
    print(f"'whisper'.upper() = {await loud.execute(ctx)}\n")

    # --- Comparisons return BoolI ---
    cmp = IntI(42) > 10
    print(f"42 > 10 = {await cmp.execute(ctx)}")
    print(f"  type: {type(cmp).__name__}")  # BoolI

    eq = StrI("abc").eq("abc")
    print(f"'abc'.eq('abc') = {await eq.execute(ctx)}\n")

    # --- Logical ---
    both = BoolI(True).and_(BoolI(False))
    print(f"True AND False = {await both.execute(ctx)}")

    either = (IntI(5) > 10).or_(IntI(3) < 7)
    print(f"(5 > 10) OR (3 < 7) = {await either.execute(ctx)}\n")

    # --- Tree inspection ---
    tree = (IntI(2) ** 10) > 1000
    print("Tree: (2 ** 10) > 1000")
    print_tree(tree)
    print(f"= {await tree.execute(ctx)}")
    print(f"Pure: {tree.is_subtree_pure}")


asyncio.run(main())
