"""nu.std.itertools - hand-written StreamQuery atoms mirroring Python's itertools.

Builds a few itertools pipelines as Nu Forms and runs them through the engine,
printing the materialized result next to the value Python's ``itertools`` gives.

Iterator results are materialized with a ``CollectQuery`` over the Form's stream
child (``IteratorForm.to_list()`` is not yet wired through the cardinality laws).
Higher-order members read the current item via ``AttrRef("item")`` built up with
core comparison / arithmetic atoms.
"""

from __future__ import annotations

import itertools as pit

from nu import AnyAttrRef
from nu.core import CollectQuery
from nu.lang.helpers import run
from nu.std.itertools import (
    accumulate,
    chain,
    combinations,
    count,
    islice,
    pairwise,
    product,
    takewhile,
    zip_longest,
)


def show(label: str, form: object, expected: object) -> None:
    """Run a Form's stream to a list and print it beside the host result."""
    value, _ = run(CollectQuery(form._children[0]))  # type: ignore[attr-defined]
    flag = "ok" if value == expected else "MISMATCH"
    print(f"{label:24} {value!r:38} {flag}")


def main() -> None:
    """Run the itertools showcase."""
    show("chain", chain([1, 2], [3, 4]), list(pit.chain([1, 2], [3, 4])))
    show(
        "islice(start,stop,step)",
        islice(range(10), 1, 9, 2),
        list(pit.islice(range(10), 1, 9, 2)),
    )
    show(
        "count + islice",
        islice(count(100, 5), 4),
        list(pit.islice(pit.count(100, 5), 4)),
    )
    show(
        "product",
        product([1, 2], ["a", "b"]),
        list(pit.product([1, 2], ["a", "b"])),
    )
    show(
        "combinations",
        combinations([1, 2, 3, 4], 2),
        list(pit.combinations([1, 2, 3, 4], 2)),
    )
    show("pairwise", pairwise([1, 2, 3, 4]), list(pit.pairwise([1, 2, 3, 4])))
    show(
        "takewhile(item < 4)",
        takewhile(AnyAttrRef("item") < 4, [1, 2, 3, 9, 1]),
        list(pit.takewhile(lambda x: x < 4, [1, 2, 3, 9, 1])),
    )
    show(
        "zip_longest(fill=0)",
        zip_longest([1, 2, 3], [9], fillvalue=0),
        list(pit.zip_longest([1, 2, 3], [9], fillvalue=0)),
    )
    show(
        "accumulate(acc + item)",
        accumulate([1, 2, 3, 4], AnyAttrRef("acc") + AnyAttrRef("item")),
        list(pit.accumulate([1, 2, 3, 4])),
    )


if __name__ == "__main__":
    main()
