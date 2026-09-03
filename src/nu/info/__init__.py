"""nu.info -- Nu describes itself, once, from the code.

One extraction, three consumers: prompt building for an agent, an in-tree
``Info`` atom for a running agent to explore with, and the docs site. The text
they share is written in exactly one place, the code, and read from there.

Knowledge about any Nu thing comes from exactly two places, the code and the
docstring, and there is no third. So the docstring contract has a definition
rather than a taste: it is the set of facts that must be written *because they
cannot be read*. Anything the code already states is derived.

- ``core.docstring`` reads what was written.
- ``core.source`` reads what the code says.
- ``core.contract`` says which written facts are required, merges the two
  sources where a question needs both, and checks the result.
- ``record`` is the base every catalogue entry shares.
- ``interaction`` and its future siblings specialize all of it per kind.

nu.info emits structured records and formats nothing. No section titles, no
prompt styling, no rendering opinions: consumers format. It is not
``nu.inspect``, which renders a value you already have; nu.info describes what
can be written and needs no live value.
"""

from __future__ import annotations

from nu.info.core.contract import Arg, Problem
from nu.info.interaction import (
    GUIDE,
    InteractionRecord,
    catalogue,
    parse_interaction,
    validate_interaction,
)
from nu.info.record import Record


__all__ = [
    "GUIDE",
    "Arg",
    "InteractionRecord",
    "Problem",
    "Record",
    "catalogue",
    "parse_interaction",
    "validate_interaction",
]
