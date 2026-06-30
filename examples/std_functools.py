"""nu.std.functools seed: reduce as a hand-written Reduction fold.

The reducer is a Nu query reading the accumulator + item via typed AttrRefs
(IntAttrRef("acc"), IntAttrRef("item")). Hot-path e2e atom, no factory.
"""

from __future__ import annotations

from nu import IntAttrRef, run
from nu.std.functools import reduce


# 1. Product of a list (no initializer): acc starts at the first item.
e1 = reduce(IntAttrRef("acc") * IntAttrRef("item"), [1, 2, 3, 4])
print(run(e1)[0], type(e1), e1)

# 2. Sum with an initializer (acc starts at 100).
e2 = reduce(IntAttrRef("acc") + IntAttrRef("item"), [1, 2, 3], 100)
print(run(e2)[0], type(e2), e2)

# 3. Product with an initializer (acc starts at 10).
e3 = reduce(IntAttrRef("acc") * IntAttrRef("item"), [1, 2, 3, 4], 10)
print(run(e3)[0], type(e3), e3)
