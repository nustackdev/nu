"""The docstring contract, as text. The half every kind shares.

A guide is not a style guide. The contract is the set of facts that must be
written *because they cannot be read*: everything the code already states is
derived, and asking for it again only creates a second copy to go stale. That
is the test for adding a rule here, and the reason the sections are these six
and no others.

Each kind appends its own half: which sections it requires, what its subjects
have that others do not, and one conformant example.
"""

from __future__ import annotations


__all__ = ["SECTIONS"]


SECTIONS = """\
A docstring has six parts, in this order. Two are always required; the rest
are written when there is something true to put in them.

1. Summary. Required. One line, one sentence, ending in a period. What the
   thing is, at a level someone who has never seen it can act on. Do not
   restate the signature: the call form is read off the code.

2. Description. Optional, and most subjects do not have one. One or more
   paragraphs saying how it works, as continuous prose. Write it only when
   there is a mechanism the summary cannot carry. Filler here is worse than
   absence, because a reader takes it as meaningful.

   A discrete fact is not a description, it is a note. If a paragraph would
   survive being cut down to one bullet, it belongs in Notes.

3. Args. One line per argument, in order, named. Required whenever the
   subject takes any. This is often the only place the real argument list is
   written down, so it is checked against the code and a mismatch is an
   error, not a nit. Something genuinely taking any number documents them as
   one `*children` entry.

4. Notes. Optional. A bullet list of discrete facts, each standing on its own
   and each true regardless of what else is read. This is where the things no
   signature can carry belong: what is bound where, what is lazy, what
   short-circuits, what an operator does not reach. A note is not a sentence
   of the description that got moved.

5. Yields. What evaluating the subject produces, including how it behaves on
   EMPTY and INVALID when that is not the plain rule.

6. Example. Required. One worked example in doctest form, carrying the value
   it produces:

       >>> nu.run(nu.Int(10) - nu.Int(3))[0]
       7

   Doctest form is what makes an example unable to lie, so use it whenever
   the subject can run without a live fabric. Something needing a context or
   a fabric may use a plain snippet with no expected value instead.

Written by hand: those six. Read off the code and never written: the name,
the kind, the sort, the cardinality, the call form, the defaults, the module,
and the source. If you find yourself typing something the code already says,
it belongs to the parser, not to you.
"""
