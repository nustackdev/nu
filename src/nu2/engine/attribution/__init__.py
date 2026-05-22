"""Engine layer: the attribute phase.

Two modules:

- ``attributed_term`` - the ``AttributedTerm`` data model (``Path``, the
  flat columns, the ``attribute()`` factory and its sweep algorithms).
- ``attr``            - the ``Attr`` relation view plus ``Row`` / ``Rows``.

Attribution builds the data. The judging machinery lives in
``engine.validation``.
"""

from nu2.engine.attribution.attr import Attr, Row, Rows
from nu2.engine.attribution.attributed_term import AttributedTerm, Path, attribute


__all__ = [
    "Attr",
    "AttributedTerm",
    "Path",
    "Row",
    "Rows",
    "attribute",
]
