<div align="center">
  <table>
    <tbody>
      <tr>
        <td>Drop a star to support Nu ⭐</td>
        <td>
          <a href="https://discord.gg/tCa8YE7XVr">Join the Nu Discord community</a>
        </td>
      </tr>
    </tbody>
  </table>
</div>

<div align="center">
  <img width="1600" alt="Nu" src="https://github.com/user-attachments/assets/a98f0916-8867-4824-9459-bb70f16a85b6" />
  <h3>
    Nu – the interaction primitive
  </h3>
  Build apps in one primitive that spans your whole stack — databases, UIs, AI agents, and services. No glue. 50x less code.
</div>

<br/>

<div align="center">

  [![Discord](https://img.shields.io/badge/discord-join-5865F2?logo=discord&logoColor=white)](https://discord.gg/tCa8YE7XVr)
  [![Twitter Follow](https://img.shields.io/twitter/follow/nustackdev?style=social)](https://twitter.com/nustackdev)

  [![Platform Support](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-blue)]()
  [![PyPI - Python Version](https://img.shields.io/badge/python-%3E%3D%203.12-blue)](https://pypi.org/project/nustack-py/)
  [![PyPI Package](https://img.shields.io/pypi/v/nustack-py?color=yellow)](https://pypi.org/project/nustack-py/)
  [![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
  [![PyPI Downloads](https://img.shields.io/pypi/dw/nustack-py?color=green)](https://pypi.org/project/nustack-py/)

</div>

<br/>

---

<h3 align="center">
  <a href="#ℹ️-about"><b>About</b></a> &bull;
  <a href="#-quick-start"><b>Quick Start</b></a> &bull;
  <a href="#-ecosystem"><b>Ecosystem</b></a> &bull;
  <a href="#-spec"><b>Spec</b></a> &bull;
  <a href="https://github.com/nustackdev/nu/tree/main/examples"><b>Examples</b></a> &bull;
  <a href="https://nustack.dev/docs"><b>Documentation</b></a> &bull;
  <a href="#-community"><b>Community</b></a>
</h3>

---

# ℹ️ About

Every app is a set of interactions between systems: a database, a UI, AI agents, services. Nu names those interactions directly:

- **Ref** names what you touch. A KV slot, a UI widget, an LLM endpoint, a memory slot, a remote object.
- **Interaction** describes what to do with it. Read, write, branch, iterate, compose.
- **Fabric** binds Refs to a real backend. Swap the Fabric, keep the tree.

Persistence, reactivity, atomicity, observability, and scalability are inherent, not bolted on.

# 🏁 Quick Start

They say a good example is worth 100 pages of API documentation, a million directives, or a thousand words.

Well, "they" probably lie... but here's an example anyway:

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

A dashboard on a live counter that persists across restarts. One Nu tree, two Fabrics. Kill it, run again, it picks up where it left off.

## Install

Python 3.12+.

```bash
pip install "nustack-py[all]"
```

For lean installs and source builds see [nustack.dev/docs/how-to/install](https://nustack.dev/docs/how-to/install).

## Run

Save the snippet above as `app.py`, then:

```bash
python app.py
```

Open the browser tab that pops up — the counter ticks once a second, the dashboard mirrors it live.

More in [`examples/`](examples/). Full walkthrough at [nustack.dev/docs](https://nustack.dev/docs).

# 🌍 Ecosystem


## Fabrics

Each fabric binds Refs to a real backend and unlocks a new capability.

| Fabric | What |
| --- | --- |
| [`nu.mem`](https://nustack.dev/docs/reference/fabrics/mem) | In-memory state fabric. Perfect for cache, hot state, and in-process coordination. |
| [`nu.v`](https://nustack.dev/docs/reference/fabrics/virtuals) | Persistent state fabric. Refs over a KV backend (RocksDB, LMDB); transactions, snapshots, and change notifications, built in. |
| [`nu.ui`](https://nustack.dev/docs/reference/fabrics/ui) | Web UI fabric. Same fabric shape as the others, but the Refs are widgets — text, buttons, tables — rendered in the browser and live-updated as your state changes. |
| [`nu.invisibles`](https://nustack.dev/docs/reference/fabrics/invisibles) | Network fabric. Puts other fabrics on the network — bind a fabric in one process, use it from another; same Refs, same interactions, over TCP or Unix socket. |
| [`nu.ray`](https://nustack.dev/docs/reference/fabrics/ray) | Cluster compute fabric. Teleport a Nu tree to any worker in your Ray cluster; it runs there and returns the result. |

## Apps built on Nu

End-user tools written as Nu programs.

| Repo | What |
| --- | --- |
| [nustackdev/nulog](https://github.com/nustackdev/nulog) | Pure-Python, serverless logger and metrics store. Log and observe metrics from any Python code; entries persist to an embedded KV store and scale to billions, in-process. One line boots a live viewer. |

# 📐 Spec

Nu is a reference implementation of the interaction model — a language-agnostic specification of what an interaction is, how Refs name locations, and how Interactions compose into programs.

[nustackdev/interaction-model](https://github.com/nustackdev/interaction-model)

# 🛣️ Roadmap

TODO.

# 👥 Community

## Nu README badge

Add a Nu badge to your README if you're building on Nu:

[![Nu](https://img.shields.io/badge/built%20with-Nu-%237A4CE0)](https://github.com/nustackdev/nu)

```
[![Nu](https://img.shields.io/badge/built%20with-Nu-%237A4CE0)](https://github.com/nustackdev/nu)
```

## Contributing to Nu

Considering contributing to Nu? Start by opening an issue or a PR — the codebase is small and readable, and the model is stable enough to build on.

## More questions?

1. [Read the docs](https://nustack.dev/docs)
2. [Open a feature request or report a bug](https://github.com/nustackdev/nu/issues)
3. [Join the Discord community](https://discord.gg/tCa8YE7XVr)

# License

Apache-2.0
