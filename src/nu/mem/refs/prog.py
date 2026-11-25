"""mem program leaf: Nu source stored in a slot, runnable from it.

The stored form is the value form (source text on both sides), so the leaf
carries an interface rather than a codec: the ``Program`` surface.
"""

from __future__ import annotations

from nu.prog.forms import ProgramSurface

from .items import ItemRef


__all__ = ["ProgramRef"]


class ProgramRef(ItemRef, ProgramSurface):
    """A slot holding Nu program source, with the Program verbs on it.

    The stored value is Python source text defining ``out()``, and the same
    text on both sides: no codec, unlike the ``std`` refs whose domain type
    the substrate cannot hold. What the ``Program`` surface adds is the
    interface - ``load`` constructs the tree the source describes, ``run``
    constructs it and evaluates it - so a program becomes a field like any
    other, written and rewritten while the app is up.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Reading the ref yields the source verbatim; the ``Program`` calls
          are what turn it into a tree.
        - ``run`` on a slot that was never written raises: construction
          gets NULL where it wants source.

    Yields:
        The stored source text.

    Example:
        >>> class App(nu.Shape):
        ...     job = nu.ProgramRef.slot()
        >>> source = '''
        ... import nu
        ...
        ... def out():
        ...     return nu.Add(1, 2)
        ... '''
        >>> ctx = nu.Context().bind(dict, {}, App)
        >>> _ = nu.run(App.job.set(source), ctx)
        >>> nu.run(App.job.run(), ctx)[0]
        3
    """
