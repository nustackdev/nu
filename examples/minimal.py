"""Minimal Nu sketches. One pattern per section. Each runs standalone."""

import nu
from nu import runtime


# --- typed expression: arithmetic flows into a Command ---
runtime.execute(nu.Print(nu.IntI(5) + 10))


# # --- sequential composition: Commands run in order ---
runtime.execute(nu.Print(1) >> nu.Print(2) >> nu.Print(3))


import time


s = time.perf_counter()
runtime.execute(
    nu.Print(
        nu.Last(
            nu.Map(
                nu.Map(
                    nu.Iter(range(10000)),
                    transform=nu.IntAttrRef("item") * 2,
                ),
                transform=nu.IntAttrRef("item2") * 2,
                item="item2",
            )
        )
    )
    & nu.Print("12")
)
pp = f"{(time.perf_counter() - s):5f}"


s = time.perf_counter()
a = []
for i in range(10000):
    a.append(i * 2)
for j in range(10000):
    a[j] = a[j] * 2
print(f"{(time.perf_counter() - s):5f}")
print(pp)

# import time

# s = time.perf_counter()
# runtime.collect(nu.ForRange(1, 100000, nu.Print(nu.IntAttrRef("i")), index="i"))
# pp = f"{(time.perf_counter() - s):5f}"


# s = time.perf_counter()
# for i in range(100000):
#     print(i)
# print(f"{(time.perf_counter() - s):5f}")
# print(pp)

# # --- parallel composition: Commands run concurrently ---
# runtime.execute(nu.Print("a") | nu.Print("b") | nu.Print("c"))


# # --- counted loops, parallelized ---
# runtime.execute(
#     nu.ForRange(0, 100, nu.Print(nu.IntAttrRef("i")), index="i")
#     | nu.ForRange(0, 100, nu.Print(nu.IntAttrRef("j")), index="j")
#     | nu.ForRange(0, 100, nu.Print(nu.IntAttrRef("k")), index="k"),
#     max_parallel=3,
# )


# # --- branch: IfDo runs the chosen branch ---
# runtime.execute(nu.IfDo(nu.Literal(True), nu.Print("then"), nu.Print("else")))


# # --- iteration: ForRange binds the index via AttrRef and runs the body ---
# i = nu.IntAttrRef("i")
# runtime.execute(nu.ForRange(0, 3, nu.Print(i + 10), index="i"))
