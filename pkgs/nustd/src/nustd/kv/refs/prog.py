"""kv program leaf: Nu source stored in a slot, runnable from it.

The stored form is the value form (source text on both sides), so the leaf
carries an interface rather than a codec: the ``Program`` surface.
"""

from __future__ import annotations

from nu.prog import ProgramSurface

from .items import ItemRef


__all__ = ["ProgramRef"]


class ProgramRef(ItemRef, ProgramSurface):
    """A Nu program stored as source text in a KV leaf, with the Program verbs.

    Reading it yields the source verbatim, the same as any str leaf. What the
    Program surface adds is the ability to turn that stored text into a tree
    and run it, so a program becomes a value a shape can hold, write and
    replace at run time.

    Notes:
        - No codec: source text is both the stored form and the value form,
          unlike the std refs that translate between the two.
        - Construction errors surface when the stored source is loaded or
          run, not when it is written, so bad source stores fine.

    Example:
        class App(Shape):
            job = ProgramRef.slot()
        run(App.job.set(SOURCE), ctx)
        run(App.job.run(), ctx)
    """
