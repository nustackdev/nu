"""Minimal Nu sketches. One pattern per section. Each runs standalone."""

import nu


# --- typed expression: arithmetic flows into a Command ---
nu.Print(nu.IntI(5) + 10).execute_sync()


# --- sequential composition: yields in order ---
nu.Print(nu.Literal(1) >> nu.Literal(2) >> nu.Literal(3)).execute_sync()


# --- parallel composition: interleaved stream ---
nu.Print(nu.Literal("a") | nu.Literal("b") | nu.Literal("c")).execute_sync()


# --- identity: Nu() is the algebra's 0; absorbed in composition ---
nu.Print(nu.Nu() >> nu.Literal(42) >> nu.Nu()).execute_sync()


# --- branch: If forwards the chosen branch's stream ---
nu.Print(nu.If(nu.Literal(True), nu.Literal("then"), nu.Literal("else"))).execute_sync()


# --- iteration: ForEach binds the element via AttrRef ---
i = nu.IntAttrRef("i")
nu.ForEach(nu.Literal([10, 20, 30]), nu.Print(i + 1), item="i").execute_sync()


# --- stateful read: ctx.attrs prepopulated, Ref reads it ---
x = nu.IntAttrRef("x")
ctx = nu.Context()
ctx.attrs["x"] = 5
nu.Print(x * 10).execute_sync(ctx)


# --- collect keeps the stream as a list; execute drains it ---
app = nu.Literal("x") >> nu.Literal("y")
print(app.collect_sync())
app.execute_sync()
