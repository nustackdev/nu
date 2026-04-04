# Nu

**Write logic once. Reshape it for anything.**

A value is a Nu. An operation is a Nu. A full application is a Nu. Same primitive, same composition rules, any scale.

Implementation is Python (nustack). Ideas are language-independent.

## Show me

They say a good example is worth 100 pages of API documentation, a million directives, or a thousand words.

Well, "they" probably lie... but here's an example anyway:

```python
from nu import Context
from nu.ops import Seq, ForRange, If, Print
from nu.shapes import Shape
import nu_virtuals as ebv

# Define your data topology
class Station(Shape):
    temperature = ebv.FloatRef.slot()
    wind_speed = ebv.FloatRef.slot()

class Dashboard(Shape):
    warnings = ebv.IntRef.slot()

# Compose your logic - builds a Nu, nothing executes yet
monitor = Seq(
    Station.temperature.store(18.0),
    Station.wind_speed.store(10.0),
    Dashboard.warnings.store(0),
    ForRange(0, 100,
        Seq(
            Station.temperature.store(Station.temperature + 1.4),
            If(Station.temperature > 32.0,
                Seq(
                    Dashboard.warnings.store(Dashboard.warnings + 1),
                    Print("WARN", Station.temperature),
                ),
            ),
        ),
    ),
    Print("Total warnings", Dashboard.warnings),
)

# Reshape: wrap all storage ops in transactions automatically
monitor = ebv.auto_atomic(monitor)

# Evaluate against any Substrate
ctx = Context().bind(storage, StorageProtocol)
await monitor.execute(ctx)
```

Three things happened:

1. **Composed** - built a Nu from smaller Nus. Shapes declare data topology, Refs point to locations, Ops transform values. Nothing ran.
2. **Reshaped** - `auto_atomic` is a Deformation. It walked the composition and wrapped every storage Op in transaction.
3. **Evaluated** - bound a Substrate (RocksDB) and ran it. Swap the Substrate, get different storage. The composition stays identical.

You don't write "the in-mem version" and "the RocksDB version". You write it once.

## What falls out of this

Not features bolted on. Consequences of the model:

- **Substrate independence** - same composition runs on a dict in tests and RocksDB in production. New backend? Add a Substrate. Don't touch your programs.
- **Distribution** - send a sub-composition to another machine, evaluate there, return the result. Going from one to three machines doesn't change the program.
- **Cross-Substrate composition** - one Nu reads from a blockchain RPC, writes to RocksDB, queries a REST API. All through Refs. Integration code disappears.
- **Incremental reactivity** - the composition IS the dependency graph. When a Ref changes, you know exactly what to re-evaluate. Purity tells you what to skip.
- **Resumability** - checkpoint mid-evaluation, resume later.
- **Codegen** - compositions are inspectable data with algebraic properties. A Transformation emitting optimized code is natural.

## Why these work

Properties that make this mechanical, not magical:

- **Recursive composition** - a Value, an Op, a full application - all Nus, all compose the same way. No special top-level construct.
- **Unified address space** - Refs are typed pointers that don't assume what's behind them. Plug in a Substrate and Refs resolve there.
- **Algebraic properties** - compositions carry metadata (purity, commutativity, independence). Transformations use these to rewrite compositions by algebraic laws, not pattern matching.
- **Code is data** - a Nu is a live structure you can inspect, serialize, and transform. The composition persists after evaluation.

## Getting started

```bash
pip install nu[minimal]
```

With persistent storage:

```bash
pip install nu[default]  # includes virtuals, RocksDB, type extensions
```

Requires Python 3.12+.

## Infra

| Package | What |
|---------|------|
| **[virtuals](https://github.com/nustackdev/virtuals)** | virtual Python collections over any storage |
| **[invisibles](https://github.com/nustackdev/invisibles)** | transparent remote method invocation |
| **[composables](https://github.com/nustackdev/composables)** | service composition and lifecycle management |

## Ecosystem

| Package | What |
|---------|------|
| **nu-virtuals** | bridges Nu Refs to virtuals Views with RocksDB backend, in-memory or text storages |
| **nu-dict** | in-memory python dict for stroage |
| **nu-distributed** | distribution via Ray + invisibles |
| **nu-datetime**, **nu-math**, **nu-fin**, **nu-uuid**, **nu-path** | type extensions |

## Status

v0.1.0. APIs will break. No backwards compatibility guarantees.

Two production systems run on Nu today:

- A financial platform processing thousands of distributed transactions per second across 2 machines
- A reactive knowledge base with persistent state and a live UI

## License

MIT
