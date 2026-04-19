"""Basic Nu example - pure arithmetic under the new evaluator.

Shows the core pattern: build a tree, open it, take the value.
"""

import asyncio

import nu


async def main() -> None:
    ctx = nu.Context()

    # Build (3 + 4) * 2
    expr = nu.MulOp(nu.AddOp(nu.Literal(3), nu.Literal(4)), nu.Literal(2))

    # single-yield value via `first`
    print(f"(3 + 4) * 2 = {await nu.first(expr, ctx)}")

    # `collect` gives a list (one element for a yield-once tree)
    print(f"collect: {await nu.collect(expr, ctx)}")

    # `execute` drains and returns None (algebra-faithful)
    result = await nu.execute(expr, ctx)
    print(f"execute returns: {result}")

    # Sequential composition with `>>`
    seq = nu.Literal(1) >> nu.Literal(2) >> nu.Literal(3)
    print(f"1 >> 2 >> 3 collect: {await nu.collect(seq, ctx)}")

    # Parallel composition with `|` (interleaves)
    par = nu.Literal("a") | nu.Literal("b") | nu.Literal("c")
    print(f"a | b | c collect: {sorted(await nu.collect(par, ctx))}")

    # Purity
    print(f"Pure: {nu.is_pure(expr)}")

    # Control flow: If branches, forwards the chosen branch's stream.
    cond_true = nu.If(nu.Literal(True), nu.Literal("then!"), nu.Literal("else"))
    cond_false = nu.If(nu.Literal(False), nu.Literal("then"), nu.Literal("else!"))
    print(f"If(True): {await nu.first(cond_true, ctx)}")
    print(f"If(False): {await nu.first(cond_false, ctx)}")

    # If forwarding a multi-yield branch
    branch = nu.Literal("x") >> nu.Literal("y") >> nu.Literal("z")
    forwarded = nu.If(nu.Literal(True), branch)
    print(f"If forwards stream: {await nu.collect(forwarded, ctx)}")

    # Print: a Command. Yields nothing. is_pure is False (WRITE to stdio).
    app = nu.Print("hello", "world", 42) >> nu.Print("done")
    print(f"app Commands yield: {await nu.collect(app, ctx)}")
    print(f"app is_pure: {nu.is_pure(app)}  (WRITE to stdio)")
    await nu.execute(app, ctx)

    # Query: read from ctx.attrs. Yields one value.
    ctx2 = nu.Context()
    ctx2.attrs["greeting"] = "hola"
    greeting_ref = nu.StrAttrRef("greeting")
    print(f"AttrGet via first: {await nu.first(greeting_ref, ctx2)}")
    # AttrExistsOp is a pure Query too
    from nu.context.attr_ops import AttrExistsOp
    print(f"'greeting' exists: {await nu.first(AttrExistsOp(greeting_ref), ctx2)}")
    print(f"'missing' exists: {await nu.first(AttrExistsOp(nu.StrAttrRef('missing')), ctx2)}")


asyncio.run(main())
