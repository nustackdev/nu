"""Example parsing: an example section in, code and expected output out.

Two forms are accepted. Doctest form carries the value the example produces,
so it can be executed and cannot lie about what it does::

    >>> nu.run(nu.Int(10) - nu.Int(3))
    7

Plain form is a snippet with no expected value, for an atom that needs a live
fabric or context to run at all::

    nu.Print(nu.Str("hi"))

Which one an example uses is recorded rather than judged. Whether a plain
example is acceptable for a given atom is a Nu question, so it belongs to the
per-kind validator upstairs, not here.
"""

from __future__ import annotations

from dataclasses import dataclass


__all__ = [
    "Example",
    "parse_example",
    "parse_examples",
]

_PROMPT = ">>> "
_CONTINUATION = "... "


@dataclass(frozen=True)
class Example:
    """One worked example: what to run, and what it produces."""

    code: str = ""
    expected: str = ""
    doctest: bool = False
    raw: str = ""

    def __bool__(self) -> bool:
        """True when there is anything runnable here."""
        return bool(self.code)


def parse_example(text: str) -> Example:
    """Split an example section into its code and its expected output.

    Lines prefixed ``>>>`` or ``...`` are code and everything between them is
    expected output. A section with no prompt anywhere is taken whole as code
    with no expected output.

    Args:
        text: the section body, already dedented.

    Returns:
        The parsed example. Empty text parses to an empty Example rather than
        raising, so a caller can treat absence as data.
    """
    raw = text.strip("\n")
    if not raw.strip():
        return Example(raw=raw)
    lines = [
        line for line in raw.splitlines() if line.strip() not in ("::", ".. code-block:: python")
    ]
    if not any(line.strip().startswith(">>>") for line in lines):
        return Example(code="\n".join(lines).strip("\n"), raw=raw)

    code: list[str] = []
    expected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith((_PROMPT, _CONTINUATION)):
            code.append(stripped[4:])
        elif stripped in (">>>", "..."):
            code.append("")
        else:
            expected.append(stripped)
    return Example(
        code="\n".join(code).strip("\n"),
        expected="\n".join(expected).strip(),
        doctest=True,
        raw=raw,
    )


def parse_examples(text: str) -> tuple[Example, ...]:
    """Split an Example section into one Example per blank-line-separated chunk.

    An Example section can carry more than one worked example, one after the
    other, separated by blank lines. Each chunk parses through
    :func:`parse_example`, so both doctest and plain forms are recognised
    per chunk. Chunks that are all whitespace or that parse empty are
    dropped.

    Args:
        text: the section body, already dedented.

    Returns:
        The examples in order. Empty tuple when the section is empty.
    """
    raw = text.strip("\n")
    if not raw.strip():
        return ()
    chunks: list[list[str]] = [[]]
    for line in raw.splitlines():
        if not line.strip():
            if chunks[-1]:
                chunks.append([])
        else:
            chunks[-1].append(line)
    out: list[Example] = []
    for chunk in chunks:
        if not chunk:
            continue
        example = parse_example("\n".join(chunk))
        if example:
            out.append(example)
    return tuple(out)
