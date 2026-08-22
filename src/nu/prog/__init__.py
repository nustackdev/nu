"""nu.prog: interactions over Nu programs.

The ``prog`` fabric hosts interactions whose subject is a Nu program itself.
Currently one:

- ``Eval`` -- dynamic evaluation. A scalar carrier yields a Nu term at
  runtime; Eval compiles it against the current schema, validates it against
  an optional promise, and drives it inside the current Runtime.

``nu.lang`` keeps the vocabulary Eval leans on (``Sort.DYNAMIC``,
``Attr.HAS_DYNAMIC``) but has no knowledge of Eval itself. Importing
``nu.prog`` registers Eval's placement law (``eval_carrier_is_scalar``) into
``nu.lang.laws.LAWS``.
"""

from __future__ import annotations

from .eval import Eval
from .eval_promise import EvalPromiseError


__all__ = ["Eval", "EvalPromiseError"]


# Register the prog laws with ``nu.lang.laws.LAWS`` at import time. LAWS is a
# mutable list on the lang side; every consumer reads it live. Kept guarded so
# a re-import (e.g. reloading during tests) does not double-add.
def _register_prog_laws() -> None:
    from nu.lang import laws as _lang_laws

    from .laws import LAWS as PROG_LAWS

    if getattr(_lang_laws, "_prog_laws_registered", False):
        return
    _lang_laws.LAWS.extend(PROG_LAWS)
    _lang_laws._prog_laws_registered = True


_register_prog_laws()
