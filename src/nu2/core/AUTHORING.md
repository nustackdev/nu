# Authoring a core atom

How to port a v1 atom onto the v2 engine. Copy the golden examples; do not
invent a style. Every atom is a `Term` subclass that declares its attributes
and emits a thunk.

## Where things live

- **`core/` is Python builtins only.** Value ops, stream lenses, folds,
  reflection, the dynamic escape hatches. No Context, no fabric, no Ref I/O.
  Files are grouped by **Python domain** (`arithmetic`, `access`, `iteration`,
  `transform`, `reduction`, `dynamic`...), never by interaction kind. There is
  no `command.py` / `flow.py` / `span.py`.
- **Fabrics live in their own dir.** A Fabric is an addressable space where
  Refs live. The Context fabric is `nu2/context/`: its Ref (`AttrRef`) in
  `refs.py`, its write interactions (`Set`, `Delete`) in `ops.py`. Other
  fabrics (virtuals, mem, substrate) follow the same shape. Anything that
  reads or writes a fabric belongs with that fabric, not in `core`.
- **Refs are per-fabric. There is no fabric-less Ref.** The abstract `Ref`
  kind in `nu2.lang` carries only sort + cardinality; concrete Refs (AttrRef,
  later service / shape Refs) supply the read / write against their fabric.
- **Flows and Spans are a later pass** with their own home, not `core`.

## The contract

A compiled program is a column of thunks. The engine walks children-first and
calls `term.compile(nid, child_thunks)` / `term.acompile(nid, child_athunks)`;
each returns a thunk that closes over its child thunks.

```python
def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
    left, right = children            # child thunks, in slot order
    def thunk(rt: Runtime) -> object:
        a = left(rt)                  # call a child thunk to get its value
        return a + right(rt)
    return thunk
```

Rules:
- **Implement both** `compile` and `acompile`. The async twin mirrors the sync
  one with `await` on each child thunk.
- `self.children` (child Terms) and `self.payload` are reachable in `compile`.
- A child thunk is lazy: it runs only when called.
- Propagate sentinels: an operand that `is EMPTY or is INVALID` collapses a
  value to `INVALID` (see `arithmetic.py`).

## Children vs payload

- **payload is for intrinsic constants only** - a Literal's value, a static
  Ref's name. Opaque, never traversed.
- **Anything Nu-computable is a child.** A key, an index, a loop-var name can
  be a Ref resolved elsewhere, so it must be a traversable child, never a
  payload entry. `Map(source, transform, key="item")` wraps `"item"` into a
  `Literal` child; pass a Ref instead and the name is computed at runtime.

## State (fabrics only)

Core never touches Context. Fabric interactions do, and they go **through the
Ref**, so the write mechanism lives with the fabric:

```python
# context/refs.py - the fabric owns read + write
class AttrRef(Ref):
    def compile(self, nid, children):
        name = self.payload["name"]
        return lambda rt: rt.ctx.attrs.get(name, EMPTY)
    def write(self, rt, value): rt.ctx.attrs[self.payload["name"]] = value

# context/ops.py - the Command delegates to the ref, declares the slot
class Set(Command):
    mutates = Declared(value=frozenset({0}))
    def compile(self, nid, children):
        ref = self.children[0]; value = children[1]
        def thunk(rt):
            v = value(rt)
            if v is EMPTY or v is INVALID: return
            ref.write(rt, v)
        return thunk
```

The mutation slot holds a Ref; `mutates` declares it so the effect synthesis
binds it WRITE. Every other slot is a read.

The one exception is the **loop-variable side-channel**: `Map` / `Filter` bind
each item with `rt.ctx.attrs[name] = elem` before evaluating the body. This is
the model's designated channel for short-lived loop vars (read back via
`AttrRef`), not a tracked fabric write. See `transform.py`.

## Streams

A stream atom's thunk **returns an iterator** (a generator). Use `_stream.py`:
`sync_iter(value)` (sync, sentinel-as-empty) and `aiter_any(value)` (sync or
async). Sources build one (`Iter`), lenses pull and re-yield (`Map`,
`Filter`), folds drain to a scalar (`Sum`, `Collect`); a `Reduction` must have
a stream child.

## Golden examples by shape

| Shape | Atom | File |
|-------|------|------|
| scalar value op | `Add` | `core/arithmetic.py` |
| stream source | `Iter` | `core/iteration.py` |
| stream lens (item via child key) | `Map`, `Filter` | `core/transform.py` |
| reduction (stream -> scalar) | `Sum`, `Collect` | `core/reduction.py` |
| fabric Ref (read + write) | `AttrRef` | `context/refs.py` |
| fabric command | `Set`, `Delete` | `context/ops.py` |
| host escape hatch | `Globals`, `Exec` | `core/dynamic.py` |

## Porting recipe (v1 -> v2)

1. Find the v1 source (each domain file's docstring names it).
2. Is it a value/stream op over data? -> `core`, by domain. Does it read/write
   a fabric? -> that fabric's dir. A type (range, int, list)? -> a Form (later).
3. Pick the kind by behavior: yields one value -> `ScalarQuery`; yields a
   stream -> `StreamQuery`; folds a stream -> `Reduction`; writes -> `Command`;
   writes and yields -> `ScalarAction` / `StreamAction`.
4. Translate mechanics to a thunk: v1 `child.eval(ctx)` -> call the child
   thunk; `child.open(ctx)` -> iterate it.
5. Declare attributes the kind needs (`mutates`, algebra flags). Keys / names
   are children, not payload.

Do not port: callable-taking `*Fn` variants (function injection is deferred),
and anything the v2 taxonomy drops.

## Tests

One file per domain (`tests/nu2/core/test_<domain>.py`); fabric tests under
`tests/nu2/context/`. For an implemented atom: build a program, `run` it
against a `Context`, assert value + mutation. Keep structural tests (sort /
cardinality / law conformance, no eval) for siblings still stubbed.

Before finishing: `.venv/bin/python -m pytest tests/nu2 -q` green, and
`.venv/bin/python -m ruff check` / `ruff format --check` clean. Use the
project venv, never bare `pytest` / `ruff`.
