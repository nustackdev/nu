"""Holding pen for the old sort-grouped core modules.

These are the previous nu2 core files, grouped by interaction sort
(``arithmetic``, ``commands``, ``flows``, ...). They are parked here during the
core restructure: the new ``nu2.core`` groups atoms by Python domain (one file
per logical family, crossing sorts) rather than by sort. ``nu2.core.__init__``
still re-exports from here transitionally so existing callers keep working;
each name moves to its new domain module as the agents implement it, and this
package is deleted once the move is complete.

Reference only - do not build new atoms here.
"""
