"""Minimal Nu sketches. One pattern per section. Each runs standalone."""

import asyncio

import nu


# --- typed expression: arithmetic flows into a Command ---
asyncio.run(nu.Print(nu.IntI(5) + 10).execute())


# --- sequential composition: yields in order ---
asyncio.run(nu.Print(nu.Literal(1) >> nu.Literal(2) >> nu.Literal(3)).execute())


# --- parallel composition: interleaved stream ---
asyncio.run(nu.Print(nu.Literal("a") | nu.Literal("b") | nu.Literal("c")).execute())


# --- real concurrency: three Delays in parallel finish in 1s, not 3s ---
app = (
    (nu.Delay(1) >> nu.Literal(1)) | (nu.Delay(1) >> nu.Literal(2)) | (nu.Delay(1) >> nu.Literal(3))
)
asyncio.run(nu.Print(app).execute())


# --- identity: Nu() is the algebra's 0; absorbed in composition ---
asyncio.run(nu.Print(nu.Nu() >> nu.Literal(42) >> nu.Nu()).execute())


# --- branch: If forwards the chosen branch's stream ---
asyncio.run(nu.Print(nu.If(nu.Literal(True), nu.Literal("then"), nu.Literal("else"))).execute())


# --- iteration: ForEach binds the element via AttrRef ---
i = nu.IntAttrRef("i")
asyncio.run(nu.ForEach(nu.Literal([10, 20, 30]), nu.Print(i + 1), item="i").execute())


# --- stateful read: ctx.attrs prepopulated, Ref reads it ---
x = nu.IntAttrRef("x")
ctx = nu.Context()
ctx.attrs["x"] = 5
asyncio.run(nu.Print(x * 10).execute(ctx))


# --- collect keeps the stream as a list; execute drains it ---
app = nu.Literal("x") >> nu.Literal("y")
print(asyncio.run(app.collect()))
asyncio.run(app.execute())
