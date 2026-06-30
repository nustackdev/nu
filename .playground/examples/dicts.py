"""Dict gradient. Each section runs standalone."""

import nu
from nu import runtime


i = nu.IntAttrRef("item")
k = nu.StrAttrRef("item")


# 1. Build a dict and get a value by key.
prices = nu.DictForm({"AAPL": 180, "GOOG": 140, "TSLA": 250})
runtime.execute(nu.Print(prices["AAPL"]))


# 2. Iterate keys, print each.
runtime.execute(nu.ForEachDo(nu.Iter(prices.keys()), nu.Print(k)))


# 3. Iterate values, sum.
total = nu.Sum(nu.Collect(nu.Iter(prices.values())))
runtime.execute(nu.Print("total:") >> nu.Print(total))


# 4. Filter values, keep entries with value >= 180. Print the surviving values.
runtime.execute(
    nu.ForEachDo(
        nu.Filter(nu.Iter(prices.values()), condition=(i >= 180)),
        nu.Print(i),
    )
)


# 5. Build a dict from a range. Map i -> i*i for 0..5.
squares = nu.DictForm(
    nu.ToDict(nu.Iter(range(5)), key=i, value=i * i),
)
runtime.execute(nu.Print(squares))
runtime.execute(nu.Print(squares[3]))
