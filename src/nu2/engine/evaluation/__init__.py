"""Engine layer: the evaluation contract.

The engine's evaluation layer is a single Protocol -- :class:`Runtime` --
that declares the dispatch shape a compiled Program is driven through.
The engine ships no concrete runtime, no budget primitives, no
concurrency toolkit; those belong to whichever language layer drives the
Program (Nu's concrete implementation lives in ``nu2.lang.evaluation``).
"""

from .protocol import Runtime


__all__ = ["Runtime"]
