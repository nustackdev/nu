# Nu

Assemble software, don't write it.

Nu program is an Interaction over Refs composed as a tree:

- **Ref** names any resource. A KV item, a UI widget, a remote endpoint, a memory slot.
- **Interaction** is the work over Refs. Read, write, compute, branch, iterate, compose.
- **Fabric** implements Refs against a concrete backend. Swap Fabrics, keep the tree.

Distribution, persistence, reactivity, atomicity, and observability come out as tree transformations.

50x less code for humans, 50x less tokens for agents, than writing it line by line in imperative Python.

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
        nu.IfDo(Counter.value.missing(), Counter.value.store(0))
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

```bash
pip install nu[minimal]      # core language only
pip install nu[default]      # + virtuals, RocksDB, types
pip install nu[nudle]        # + UI fabric
pip install nu[distributed]  # + Ray + invisibles
```

Python 3.12+.

## Apps built on Nu

- [nulog](https://github.com/nustackdev/nulog). Structured logging as a Nu app. Handles billions of entries, UI dashboard out of the box.

## Status

v0.1.0. APIs will break, no backwards compatibility guarantees.

## License

Apache-2.0
