"""nu.info -- Nu describes itself, once, from the code.

One extraction, three consumers: prompt building for an agent, an in-tree
``Info`` atom for a running agent to explore with, and the docs site. The
text they share is written in exactly one place, the code, and read from
there.

Knowledge about any Nu thing comes from exactly two places, the code and the
docstring, and there is no third. So the docstring format has a definition
rather than a taste: it is the set of facts that are worth writing *because
they cannot be read*. Anything the code already states is derived. Absence of
a written section is not an error: it is empty data on the record, and the
consumer decides. Only lies about the code, or malformed sections, are
violations.


The Nu docstring format
-----------------------

A docstring has six parts, in this order. Each is written when there is
something true to put in it; every part is optional in the sense that its
absence is not flagged.

1. Summary. One line, one sentence, ending in a period. What the thing is,
   at a level someone who has never seen it can act on. Do not restate the
   signature: the call form is read off the code.

2. Description. One or more paragraphs saying how it works, as continuous
   prose. Write it when there is a mechanism the summary cannot carry.
   Filler here is worse than absence, because a reader takes it as
   meaningful.

   A discrete fact is not a description, it is a note. If a paragraph would
   survive being cut down to one bullet, it belongs in Notes.

3. Args. One line per argument, in order, named. Often the only place the
   real argument list is written down for an atom that inherits the variadic
   constructor. When present, it is checked against the code and a mismatch
   is a violation.

4. Notes. A bullet list of discrete facts, each standing on its own. Where
   things no signature can carry belong: what is bound where, what is lazy,
   what short-circuits, what an operator does not reach. A note is not a
   sentence of the description that got moved.

5. Yields. What evaluating the subject produces, including how it behaves on
   EMPTY and INVALID when that is not the plain rule. On an atom the return
   annotation is missing, so the docstring is where the yield type lives; on
   a method the return annotation is authoritative and this section is
   redundant.

6. Example. One worked example in doctest form, carrying the value it
   produces:

       >>> nu.run(nu.Int(10) - nu.Int(3))[0]
       7

   Doctest form is what makes an example unable to lie, so use it whenever
   the subject can run without a live fabric. Something needing a context or
   a fabric may use a plain snippet with no expected value instead.

Written by hand: those six. Read off the code and never written: the name,
the kind, the sort, the cardinality, the call form, the defaults, the
module, and the source. If you find yourself typing something the code
already says, it belongs to the parser, not to you.


The layout
----------

- ``core.docstring`` reads what was written.
- ``core.source`` reads what the code says.
- ``core.contract`` says what a written fact may not lie about, and merges
  the two sources where a question needs both.
- ``record`` is the base every catalogue entry shares.
- ``interaction``, ``call`` and ``builder`` specialize the record per kind.

nu.info emits structured records and formats nothing.
"""

from __future__ import annotations

from nu.info.builder import BuilderRecord, parse_builder, verify_builder
from nu.info.call import CallRecord, parse_call, verify_call
from nu.info.core.contract import Arg, Violation
from nu.info.interaction import (
    InteractionRecord,
    catalogue,
    parse_interaction,
    verify_interaction,
)
from nu.info.record import Record


__all__ = [
    "Arg",
    "BuilderRecord",
    "CallRecord",
    "InteractionRecord",
    "Record",
    "Violation",
    "catalogue",
    "parse_builder",
    "parse_call",
    "parse_interaction",
    "verify_builder",
    "verify_call",
    "verify_interaction",
]
