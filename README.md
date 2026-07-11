# Nu

Nu is a programming model. You describe your program as an interaction over named resources; Nu evaluates it against a Context that binds those resources to concrete backends. Distribution, reactivity, durability, atomicity and observability fall out as tree transformations — not framework layers.

Two citizens make up every program:

- **Ref** — a typed pointer to a resource: a db row, a config key, an in-memory slot, a browser DOM node, an RPC endpoint. Carries the address, not the value.
- **Interaction** — what a program does with Refs (and with other Interactions): read, write, compute, branch, iterate, compose.

A **Fabric** is what actually resolves Refs and carries out Interactions (rocksdb, an in-memory dict, a websocket, ...). The **Context** is the bag of Fabrics your program runs against. Same program, different Context → different world (test, staging, prod, another machine).

Full model: see [nustackdev/nu/docs](docs/) and the design space in Gor's Go.

## Install

```bash
pip install nu[minimal]     # core language only
pip install nu[default]     # + virtuals, RocksDB, type extensions
pip install nu[nudle]       # + UI fabric (browser tab as a Ref surface)
pip install nu[distributed] # + Ray + invisibles
```

Python 3.12+.

## Example

```python
import nu
import nu.virtuals as v
from virtuals import Navigator
from virtuals.tkv.storage import TransactionProtocol

class Order(nu.Shape):
    symbol = v.StrRef.slot()
    price  = v.FloatRef.slot()
    qty    = v.IntRef.slot()

program = nu.Sequential(
    Order.symbol.store("AAPL"),
    Order.price.store(185.5),
    Order.qty.store(10),
    nu.print("notional:", Order.price * Order.qty),
)

with v.text_storage("/tmp/orders") as storage:
    nav = Navigator(storage)
    with storage.transaction() as tx:
        ctx = nu.Context().bind(Navigator, nav).bind(TransactionProtocol, tx)
        await nu.arun(v.auto_atomic(program), ctx)
```

Same `program`, swap the Context and it runs against an in-memory dict, a browser tab, or a remote process — see the fabrics below. More end-to-end examples in [`examples/`](examples/).

## Fabrics

A fabric is a Ref/Interaction implementation over one backend. Nu ships three in-tree:

| Fabric         | Backend                       | What                                                                        |
| -------------- | ----------------------------- | --------------------------------------------------------------------------- |
| `nu.mem`       | plain Python dict             | zero-dependency, sync+async, ideal for tests, fixtures, in-process state    |
| `nu.virtuals`  | [virtuals](https://github.com/nustackdev/virtuals) views over any storage (RocksDB, LMDB, in-memory, text) | durable and reactive: Refs read/write disk, `.on_change()` yields live subscriptions |
| `nu.ui`        | browser tab (websocket)       | UI fabric — Pages are Shapes, widgets are Refs, mutations become React state |

Each fabric ships its own typed Refs (`IntRef`, `StrRef`, `ListRef`, `ShapesListRef`, …) matching the same protocol; you swap the import to move a program between substrates.

## Infra

Independent libraries Nu builds on. Each knows nothing about Nu; a small bridge in `nu.<fabric>` connects the two.

| Lib                                                         | What                                                                   |
| ----------------------------------------------------------- | ---------------------------------------------------------------------- |
| [virtuals](https://github.com/nustackdev/virtuals)          | virtual Python collections over any storage — the substrate for durable Shapes |
| [invisibles](https://github.com/nustackdev/invisibles)      | transparent remote method invocation — sync stays sync, async stays async |
| [composables](https://github.com/nustackdev/composables)    | async service composition and lifecycle — the runtime backbone that wires substrates, transports, coordinators together |

`nu.distributed` composes all three to make Nus location-independent.

## Status

v0.1.0. APIs will break, no backwards compatibility guarantees.

Two production systems run on Nu today:

- A financial platform processing thousands of distributed transactions per second across two machines
- A reactive knowledge base with persistent state and a live UI

## License

MIT
