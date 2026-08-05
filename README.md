# Nu

The interaction primitive.

Build apps in one primitive that spans your whole stack (databases, UIs, AI agents, and services). No glue. 50x less code.

Every app is a set of interactions between systems: a database, a UI, AI agents, and services. Nu makes interaction the primitive:

- **Ref** names what you touch. A KV slot, a UI widget, an LLM endpoint, a memory slot, a remote object.
- **Interaction** describes what to do with it. Read, write, branch, iterate, compose.
- **Fabric** binds Refs to a real backend. Swap the Fabric, keep the tree.

Persistence, reactivity, atomicity, observability, and scalability are inherent, not bolted on.

## The interaction model

Nu, the one core atom, splits into two:

- **Ref**: address to any resource.
- **Interaction**: the work over Refs.

Interaction has five kinds:

- **Query**: pure evaluation, yields values.
- **Command**: mutation, yields nothing.
- **Action**: mutation, yields values.
- **Span**: scope wrapping a body.
- **Flow**: orchestration of mutations.

Compose them into a tree. That is a Nu program.

## Example

A dashboard on a live counter that persists across restarts. One Nu tree, two Fabrics.

```python
import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class Dashboard(nu.ui.Page):
    count: nu.ui.TextRef


class App(nu.ui.Index):
    pages = nu.ui.Pages({"/": Dashboard})


app = nu.With(
    nu.v.presets.rocksdb_navigator(".dbtest"),
    nu.ui.presets.server(
        nu.v.auto_flow_atomic(
            nu.ReactForever(
                Counter.value.on_change(),
                Dashboard.count.set(Counter.value),
            ),
        ),
    ),
    body=(
        nu.IfDo(Counter.value.missing(), Counter.value.set(0))
        >> nu.ForeverDo(
            Counter.value.inc() >> nu.Delay(1.0),
        )
    ),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(nu.v.auto_flow_atomic(app)))
```

Run it, open the browser tab. The counter ticks once a second, the dashboard mirrors it live. Kill it, run again, it picks up where it left off.

More examples in [`examples/`](examples/). Full walkthrough at [nustack.dev/docs](https://nustack.dev/docs).

## Fabrics

A Fabric implements Refs against one backend. Nu ships five in-tree.

| Fabric | What |
| --- | --- |
| `nu.m` | In-process substrate. Zero-config default for tests, notebooks, cache. |
| `nu.v` | Persistent substrate backed by `virtuals`. Virtual Python collections over RocksDB, LMDB, more. |
| `nu.ui` | Refs on screen. Binds Nu Refs to a live browser tab. |
| `nu.invisibles` | Location-independent Nus. Transparent RPC across processes and machines. |
| `nu.ray` | Compute across the cluster. Scale Nu on Ray without leaving the model. |

Swap the Fabric, keep the tree. Same program runs against different substrates.

## Install

From source. Python 3.12+. See [nustack.dev/docs/how-to/install](https://nustack.dev/docs/how-to/install) for the full guide (Python side, UI bundle, verify).

## Apps built on Nu

- [nulog](https://github.com/nustackdev/nulog). Structured logging as a Nu app. Handles billions of entries, UI dashboard out of the box.

## Status

v0.1.0. APIs will break, no backwards compatibility guarantees.

## License

Apache-2.0
