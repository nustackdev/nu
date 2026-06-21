# Porting a Form file (v1 -> v2)

The file already exists at `src/nu2/forms/...` as a verbatim copy of its v1
original (`src/nu/forms/...`). **Edit it in place.** Do not rewrite from scratch
and do not move it - keep every class, method, overload, and docstring; only the
imports, atom names, and (for `*_ops` files) the eval mechanics change. This
keeps the port deterministic: nothing gets dropped. Match the surrounding v2
style exactly. Never use emdash.

## Two kinds of file

1. **Builder forms** (`int_.py`, `str_.py`, `dict_.py`, the `abc/*.py`
   interfaces, ...): pure fluent builders. Each method lazy-imports a core atom
   and returns a Form wrapping it. No eval logic of their own. Golden example:
   `src/nu2/forms/primitives/bool_.py` (already ported - copy its shape).

2. **Op-atom files** (`*_ops.py`): define `ScalarQuery` / `ScalarCommand`
   classes with real eval bodies (`_apply` / `run` / `arun`). These need a real
   port to the v2 `compile` / `acompile` thunk engine. Golden examples:
   `src/nu2/core/sentinel.py` (sentinel-accepting queries),
   `src/nu2/core/reduction.py` and `src/nu2/core/access.py` (eval + sentinel
   propagation + local mutation).

## Import rewrites (both kinds)

- `from nu.terms import Form, TypedNu`           -> `from nu2.lang import Form, TypedNu`
- `from nu.terms import IntArg, StrArg, ...`      -> `from nu2.lang import IntArg, StrArg, ...`
- `from nu.terms import Nu, Arg`                  -> `from nu2.lang import Nu, Arg`
- `from nu.terms import EMPTY, INVALID, Empty, Invalid, Sentinel`
                                                  -> `from nu2.lang import EMPTY, INVALID, Empty, Invalid, Sentinel`
- `from nu import <Atom>`                         -> `from nu2.core import <Atom>` (apply renames below)
- sibling form imports stay relative (`from .bool_ import BoolForm`,
  `from .float_ import FloatForm`, `from ..primitives import BoolForm`, etc.) -
  keep them exactly as v1 has them, they map 1:1 to the v2 tree.
- `IsEmpty` / `IsInvalid` / `NotEmpty` / `NotInvalid` are core atoms:
  `from nu2.core import IsEmpty` (the `Form` base already wires `is_empty()` /
  `is_invalid()`, so leaves rarely need these directly).

All Arg aliases exist in `nu2.lang`: Arg, BoolArg, BytesArg, DictArg, FloatArg,
FrozenSetArg, IntArg, ListArg, NoneArg, SetArg, StrArg, TupleArg.

## Atom renames (v1 -> v2 core)

| v1            | v2 core   |
|---------------|-----------|
| `IdComp`      | `Is`      |
| `At`          | `GetItem` |
| `BitwiseAnd`  | `BitAnd`  |
| `BitwiseOr`   | `BitOr`   |
| `BitwiseNot`  | `BitNot`  |
| `Xor`         | `BitXor`  |
| `ToList`      | `List`    |
| `ToSet`       | `Set`     |
| `ToTuple`     | `Tuple`   |

Every other atom name is identical (Add, Sub, Mul, Div, FloorDiv, Mod, Pow, Neg,
Pos, Abs, Eq, Ne, Lt, Le, Gt, Ge, And, Or, Not, Bool, Len, Contains, Slice,
Reversed, LShift, RShift). The full v2 core export list is in
`src/nu2/core/__init__.py` `__all__` - if a name you need is not there, STOP and
report it rather than inventing one.

## Builder pattern (copy bool_.py)

A builder method is unchanged except the import line + atom name. Example:

```python
def __xor__(self, other: IntArg) -> IntForm:
    from nu2.core import BitXor          # was: from nu import Xor

    return IntForm(BitXor(self, other))  # was: Xor(...)
```

Keep `@overload` stubs, `__hash__ = object.__hash__`, default-arg `__init__`s,
and TYPE_CHECKING blocks exactly as v1 has them.

**Docstrings (v2 ruff D102).** Every public non-dunder method needs a one-line
docstring; v1 omitted many (`is_`, `and_`, sometimes the op builders). Add a
short one wherever it is missing (e.g. `"""Identity comparison: self is
other."""`). Dunder methods (`__add__`, `__gt__`, ...) are exempt, leave them
as-is.

## Op-atom pattern (the real port)

v1 atoms use `support`/`accepts_sentinels`/`own_effects` ClassVars and an
`_apply(self, ctx, ops)` (or `run`/`arun`) body. v2 atoms drop all those
ClassVars and instead implement BOTH `compile` and `acompile` returning a thunk.

### Read ops (`ScalarQuery` with `_apply`)

`ops[i]` in v1 are the already-evaluated children. In v2 you evaluate each child
thunk yourself and propagate sentinels (an `EMPTY`/`INVALID` operand collapses
the result to `INVALID`), UNLESS the v1 class set `accepts_sentinels = True` (then
do NOT guard - see sentinel_ops.py).

v1:
```python
class KeysOp(ScalarQuery):
    support = _BOTH
    def __init__(self, operand): super().__init__(operand)
    def _apply(self, ctx, ops): return ops[0].keys()
```
v2:
```python
class KeysOp(ScalarQuery):
    """Get keys view from mapping: mapping.keys()."""

    def compile(self, nid, children):  # noqa: D102
        (operand,) = children
        def thunk(rt):
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.keys()
        return thunk

    def acompile(self, nid, children):  # noqa: D102
        (operand,) = children
        async def athunk(rt):
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.keys()
        return athunk
```
Keep the v1 `__init__` only if it adds arity meaning; a plain
`super().__init__(operand)` passthrough can be dropped (the base handles it).
Multi-operand ops bind `a, b, c = children` and guard each one. Preserve any
special return values verbatim (e.g. `return INVALID` on `KeyError`,
`a.pop(b, c)` vs `a[b]` branching on a `None` default).

### Mutation ops (v1 `ScalarCommand` with `run`/`arun`)

In v2, mutating a plain Python value in place is NOT a fabric Command - it is a
local `ScalarQuery` that performs the mutation and RETURNS the mutated target so
writes compose (exactly like `SetItem`/`SetAttr` in `src/nu2/core/access.py`).
Convert each `ScalarCommand` to a `ScalarQuery`. Drop `own_effects` / the
`mutates` declaration and the `MutableMapping`/`Mapping` isinstance TypeErrors
(mirror the simpler v1 sync `run` body). Keep the class NAME unchanged (e.g.
`SetItemCmd` stays `SetItemCmd`) so the builder call sites keep working.

v1:
```python
class UpdateCmd(ScalarCommand):
    own_effects = {0: Effect.WRITE}
    def run(self, ctx):
        target = runtime.first(self._children[0], ctx)
        other = runtime.first(self._children[1], ctx)
        target.update(other)
```
v2:
```python
class UpdateCmd(ScalarQuery):
    """Update mapping with another: mapping.update(other); yields the mapping."""

    def compile(self, nid, children):  # noqa: D102
        target_t, other_t = children
        def thunk(rt):
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target.update(other)
            return target
        return thunk

    def acompile(self, nid, children):  # noqa: D102
        target_t, other_t = children
        async def athunk(rt):
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target.update(other)
            return target
        return athunk
```

`runtime.first(self._children[i], ctx)` -> call child thunk `i`. Drop the
`from nu import runtime` lazy import entirely.

## Standard v2 op-file header

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID

if TYPE_CHECKING:
    from collections.abc import Callable
    from nu2.lang.runtime import Runtime
```

(`EMPTY`/`INVALID` are also re-exported from `nu2.lang`; either import path is
fine - match what core files do: `from nu2.lang.sentinels import EMPTY, INVALID`.)

## Hard rules

- Do NOT edit any `__init__.py` (the owner assembles those after the port).
- Do NOT touch `src/nu2/lang/` or `src/nu2/core/` - read them for reference only.
- Implement BOTH `compile` and `acompile` on every op atom.
- Keep `# noqa: D102` on `compile`/`acompile` (they inherit the docstring).
- When done, run `.venv/bin/ruff check <your files>` and
  `.venv/bin/ruff format <your files>` and fix what they flag. Do not run the
  test suite (the package is not wired yet).
- Report exactly which files you wrote and anything you had to stop on.
