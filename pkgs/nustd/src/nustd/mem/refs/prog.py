"""mem program leaf: Nu source stored in a slot, runnable from it.

The stored form is the value form (source text on both sides), so the leaf
carries an interface rather than a codec. The base order is load-bearing: the
leaf comes first so the ref reads storage; see the class docstring.
"""

from __future__ import annotations

from nu.prog import Program

from .items import ItemRef


__all__ = ["ProgramRef"]


class ProgramRef(ItemRef, Program):
    """A slot holding Nu program source, with the Program verbs on it.

    The stored value is Python source text defining ``out()``, and the same
    text on both sides: no codec, unlike the ``std`` refs whose domain type
    the substrate cannot hold. What the ``Program`` mixin adds is the
    interface - ``load`` constructs the tree the source describes, ``run``
    constructs it and evaluates it - so a program becomes a field like any
    other, written and rewritten while the app is up.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Base order is load-bearing. ``ItemRef`` reaches ``RefBase``, which
          declares ``Sort.REF`` and compiles to a fabric read; ``Program``
          reaches ``TypedNu``, which declares a scalar query and compiles to
          a passthrough over child 0. Flipped, ``TypedNu`` wins both: the ref
          yields its parent ref instead of the stored value and the effect
          machinery stops seeing a fabric touch, silently.
        - Reading the ref yields the source verbatim; the ``Program`` calls
          are what turn it into a tree.
        - ``run`` on a slot that was never written raises rather than
          yielding a sentinel: construction gets EMPTY where it wants source.

    Yields:
        The stored source text. EMPTY when the slot was never written.

    Example:
        >>> class App(nu.Shape):
        ...     job = nustd.mem.ProgramRef.slot()
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
