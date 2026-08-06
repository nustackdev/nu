<img width="1600" height="333" alt="image" src="https://github.com/user-attachments/assets/a98f0916-8867-4824-9459-bb70f16a85b6" />

# Nu – the interaction primitive.

Build apps in one primitive that spans your whole stack (databases, UIs, AI agents, and services). No glue. 50x less code.

Every app is a set of interactions between systems: a database, a UI, AI agents, and services. Nu makes interaction the primitive:

- **Ref** names what you touch. A KV slot, a UI widget, an LLM endpoint, a memory slot, a remote object.
- **Interaction** describes what to do with it. Read, write, branch, iterate, compose.
- **Fabric** binds Refs to a real backend. Swap the Fabric, keep the tree.

Persistence, reactivity, atomicity, observability, and scalability are inherent, not bolted on.

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
    nu.v.rocksdb_navigator(".dbcounter"),
    nu.ui.server(
        nu.v.auto_flow_atomic(
            nu.ReactForever(
                Counter.value.on_change(),
                Dashboard.count.set(Counter.value),
            ),
        ),
    ),
    body=nu.v.auto_flow_atomic(
        nu.IfDo(Counter.value.missing(), Counter.value.set(0))
        >> nu.ForeverDo(
            Counter.value.inc() >> nu.Delay(1.0),
        )
    ),
)

if __name__ == "__main__":
    import asyncio
    asyncio.run(nu.arun(app))
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

Python 3.12+.

```bash
pip install "nustack-py[all]"
```

See [nustack.dev/docs/how-to/install](https://nustack.dev/docs/how-to/install) for lean installs and source builds.

## Apps built on Nu

- [nulog](https://github.com/nustackdev/nulog). Structured logging as a Nu app. Handles billions of entries, UI dashboard out of the box.

## Status

Alpha. APIs will break.

## License

Apache-2.0
