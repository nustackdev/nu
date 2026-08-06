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
  <a href="#-ecosystem"><b>Ecosystem</b></a> &bull;
  <a href="#-quick-start"><b>Quick Start</b></a> &bull;
  <a href="https://github.com/nustackdev/nu/tree/main/examples"><b>Examples</b></a> &bull;
  <a href="https://nustack.dev/docs"><b>Documentation</b></a> &bull;
  <a href="#-community"><b>Community</b></a>
</h3>

---

# ℹ️ About

Nu is a Python programming model that makes **interaction** the primitive.

Every app is a set of interactions between systems: a database, a UI, AI agents, services. Nu names those interactions directly:

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

More in [`examples/`](examples/). Full walkthrough at [nustack.dev/docs](https://nustack.dev/docs).

# 🌍 Ecosystem

Nu is built as a stack. In-tree fabrics ship with Nu; the infra libraries and apps live in their own repos.

## Fabrics (in-tree)

Each fabric binds Refs to a real backend. Swap the fabric, keep the tree.

| Fabric | What |
| --- | --- |
| [`nu.mem`](https://nustack.dev/docs/reference/fabrics/mem) | In-memory state on plain dicts. Zero-config default for tests, notebooks, cache. |
| [`nu.v`](https://nustack.dev/docs/reference/fabrics/virtuals) | Persistent state over RocksDB / LMDB. Transactions, snapshots, change notifications. |
| [`nu.ui`](https://nustack.dev/docs/reference/fabrics/ui) | Refs on screen. Binds Nu Refs to a live browser tab. |
| [`nu.invisibles`](https://nustack.dev/docs/reference/fabrics/invisibles) | Location-independent Nus. Transparent RPC across processes and machines. |
| [`nu.ray`](https://nustack.dev/docs/reference/fabrics/ray) | Cluster compute. Teleport a Nu tree to any Ray worker. |

## Apps built on Nu

End-user tools written as Nu programs.

| Repo | What |
| --- | --- |
| [nustackdev/nulog](https://github.com/nustackdev/nulog) | Pure-Python, serverless logger + metrics store. Billions of entries, live UI. |

## Spec

| Repo | What |
| --- | --- |
| [nustackdev/interaction-model](https://github.com/nustackdev/interaction-model) | Language-agnostic specification of the interaction primitive. |

# 🏁 Quick Start

## 1. Install

Python 3.12+.

```bash
pip install "nustack-py[all]"
```

For lean installs and source builds see [nustack.dev/docs/how-to/install](https://nustack.dev/docs/how-to/install).

## 2. Write a Nu app

```python
import nu

nu.run(nu.print("Hello, Nu!"))
```

## 3. Run it

```shell
python my_app.py
```

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
