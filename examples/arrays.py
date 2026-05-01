"""Array/stream gradient. Each section runs standalone."""

import nu
from nu import runtime


i = nu.IntAttrRef("item")


# 1. Print a range.
runtime.execute(nu.ForEachDo(nu.Iter(range(5)), nu.Print(i)))


# 2. Map, filter, print. Double each, keep multiples of 4, print.
runtime.execute(
    nu.ForEachDo(
        nu.Filter(
            nu.Map(nu.Iter(range(10)), transform=i * 2),
            condition=(i % 4 == 0),
        ),
        nu.Print(i),
    )
)


# 3. Reduce to a value. Sum of squares of 0..100.
total = nu.Sum(
    nu.Collect(
        nu.Map(nu.Iter(range(100)), transform=i * i),
    )
)
runtime.execute(nu.Print(total))


# 4. Partition and label. Split 0..20 by even/odd, print each bucket.
parts = nu.Partition(
    nu.Iter(range(20)),
    condition=(i % 2 == 0),
)
evens = nu.At(parts, 0)
odds = nu.At(parts, 1)

runtime.execute(nu.Print("evens:") >> nu.Print(evens) >> nu.Print("odds:") >> nu.Print(odds))
