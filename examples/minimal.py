"""Minimal Nu sketches. One pattern per section. Each runs standalone."""

import nu


# --- typed expression: arithmetic flows into a Command ---
nu.Print(nu.IntI(5) + 10).execute()


# --- sequential composition: yields in order ---
nu.Print(nu.Literal(1) >> nu.Literal(2) >> nu.Literal(3)).execute()


# --- parallel composition: interleaved stream ---
nu.Print(nu.Literal("a") | nu.Literal("b") | nu.Literal("c")).execute()


nu.Print(
    nu.ForRange(0, 100, nu.Print(nu.IntAttrRef("i")), index="i")
    | nu.ForRange(0, 100, nu.Print(nu.IntAttrRef("j")), index="j")
    | nu.ForRange(0, 100, nu.Print(nu.IntAttrRef("k")), index="k")
).execute(max_parallel=3)

# --- identity: Nu() is the algebra's 0; absorbed in composition ---
nu.Print(nu.Nu() >> nu.Literal(42) >> nu.Nu()).execute()


# --- branch: If forwards the chosen branch's stream ---
nu.Print(nu.IfDo(nu.Literal(True), nu.Literal("then"), nu.Literal("else"))).execute()


# --- iteration: ForEach binds the element via AttrRef ---
i = nu.IntAttrRef("i")
nu.ForEach(nu.Literal([10, 20, 30]), nu.Print(i + 1), item="i").execute()
