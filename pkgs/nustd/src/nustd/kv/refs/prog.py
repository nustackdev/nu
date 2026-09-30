"""kv program leaf: Nu source stored in a slot, runnable from it.

The stored form is the value form (source text on both sides), so the leaf
carries an interface rather than a codec. The base order is load-bearing: the
leaf comes first so the ref reads storage; see the class docstring.
"""

from __future__ import annotations

from nu.prog import Program

from .items import ItemRef


__all__ = ["ProgramRef"]


class ProgramRef(ItemRef, Program):
    """A Nu program stored as source text in a KV leaf, with the Program verbs.

    Reading it yields the source verbatim, the same as any str leaf. What the
    Program surface adds is the ability to turn that stored text into a tree
    and run it, so a program becomes a value a shape can hold, write and
    replace at run time.

    Notes:
        - No codec: source text is both the stored form and the value form,
          unlike the std refs that translate between the two.
        - The base order is load-bearing. ``ItemRef`` first makes the class a
          ref that reads storage; with ``Program`` first the passthrough
          would win and the ref would yield its parent instead of the stored
          value, silently, with no fabric touch recorded.
        - Construction errors surface when the stored source is loaded or
          run, not when it is written, so bad source stores fine.

    Example:
        class App(Shape):
            job = ProgramRef.slot()
        run(App.job.set(SOURCE), ctx)
        run(App.job.run(), ctx)
    """
