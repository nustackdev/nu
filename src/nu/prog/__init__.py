"""nu.prog: interactions over Nu programs.

The ``prog`` fabric hosts interactions whose subject is a Nu program itself:

- ``LoadNu`` -- read python source, yield the Nu term it constructs. Source
  is the authoring format and the artifact of record; a Nu tree is what it
  lowers to, one way.
- ``Eval`` -- dynamic evaluation. A scalar carrier yields a Nu term at
  runtime; Eval compiles it against the current schema, validates it against
  an optional promise, and drives it inside the current Runtime.
- ``Program`` -- the Form over source text. ``Program(src).run()`` is the
  ergonomic surface over the pair below; mixed into a substrate ref it
  becomes ``ProgramRef``, a slot whose stored string is a program.
- ``PyBrace`` -- the environment source is *constructed* in, bound on ctx
  with ``Provide``. No Nu is ever run inside a brace and nothing but plain
  data crosses into one; exactly two things come back, a Nu term or a
  Diagnostic.

``Eval(LoadNu(source))`` is the pair: load a stored program, run it.

``nu.lang`` keeps the vocabulary Eval leans on (``Sort.DYNAMIC``,
``Attr.HAS_DYNAMIC``) but has no knowledge of Eval itself. Importing
``nu.prog`` registers Eval's placement law (``eval_carrier_is_scalar``) into
``nu.lang.laws.LAWS``.
"""

from __future__ import annotations

from .brace import PyBrace
from .constructors import BraceError, Constructor, InProcess, Venv
from .diagnostics import ConstructionError, Diagnostic
from .eval import Eval
from .eval_promise import EvalPromiseError
from .forms import Program
from .load import LoadNu


__all__ = [
    "BraceError",
    "ConstructionError",
    "Constructor",
    "Diagnostic",
    "Eval",
    "EvalPromiseError",
    "InProcess",
    "LoadNu",
    "Program",
    "PyBrace",
    "Venv",
]


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
