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
  [![PyPI - Python Version](https://img.shields.io/badge/python-%3E%3D%203.10-blue)](https://pypi.org/project/nucore/)
  [![PyPI Package](https://img.shields.io/pypi/v/nucore?color=yellow)](https://pypi.org/project/nucore/)
  [![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
  [![PyPI Downloads](https://img.shields.io/pypi/dw/nucore?color=green)](https://pypi.org/project/nucore/)

</div>

<br/>

---

<h3 align="center">
  <a href="#ℹ️-about"><b>About</b></a> &bull;
  <a href="#-build-with-nu"><b>Build</b></a> &bull;
  <a href="#-quickstart"><b>Quickstart</b></a> &bull;
  <a href="#-nu-std"><b>Nu STD</b></a> &bull;
  <a href="#-apps-built-on-nu"><b>Apps</b></a> &bull;
  <a href="#-spec"><b>Spec</b></a> &bull;
  <a href="https://github.com/nustackdev/nu/tree/main/examples"><b>Examples</b></a> &bull;
  <a href="https://nustack.dev/docs"><b>Docs</b></a> &bull;
  <a href="#-community"><b>Community</b></a>
</h3>

---

# ℹ️ About

The primitive Nu is built on, in three words.

A tiny script keeps its values in memory and calls functions on them. Real apps don't stay there. Values live in a database, arrive from a browser form, render into a dashboard, get recomputed by a background job. Almost none of the code is about the values anymore — it's all interaction between systems.

**Nu makes interaction the primitive.**

- **Ref** — a name for a value, wherever it lives: a KV slot, a UI text block, an LLM endpoint, a remote object.
- **Interaction** — what you do with a Ref: read, write, branch, iterate, compose.
- **Fabric** — binds Refs to a real system. Compose as many as you need; they all speak the same primitive.

> **Same primitive, different system.** One Ref for any resource, one Interaction for any op. Setting a browser text block is the same interaction as setting a KV slot.

Nu is the reference implementation of the [interaction model](https://github.com/nustackdev/interaction-model) in Python.

# 🧱 Build with Nu

A few of Nu's fabrics — state, UIs, cluster, models. Same Python, same code shape.

### Persistent state

*Persistent state. Stores any Python type.*

Reach any value by name; it survives restarts. Same code local or sharded across a cluster.

- Serverless, scales to terabytes
- Store any Python type

```python
...
class DB(nu.Shape):
    hits = nustd.kv.IntRef.slot()

# +1 to a persistent counter
op = DB.hits.set(DB.hits + 1)

app = nu.With(
    nustd.kv.rocksdb_navigator(".db"),
    body=nustd.kv.auto_flow_atomic(op),
)
...
```

Powered by [`virtuals`](https://github.com/nustackdev/virtuals) · [`rdbpy`](https://github.com/nustackdev/rdbpy) · [`RocksDB`](https://github.com/facebook/rocksdb) · [`LMDB`](https://www.symas.com/lmdb).

### Live browser UIs

*Reactive UIs from Python.* No JS, no build step, no websocket you had to write.

A text block, a chart, a form — set them like variables, they render. Update the value, the browser updates itself.

- 50+ components out of the box
- Live updates for free

```python
...
class Dashboard(nustd.ui.Page):
    hello = nustd.ui.TextRef.slot()

# renders live in the browser
op = Dashboard.hello.set("Hello, browser.")

app = nustd.ui.serve(Dashboard, op)
...
```

Powered by [`React`](https://react.dev) · [`Zustand`](https://github.com/pmndrs/zustand).

### Distributed execution

*Same code runs local or across the cluster.* No worker pool to run.

Teleport any Nu tree to any worker; it runs there and returns the result. Where it runs is a binding, not a rewrite.

- Same code, local or remote
- Distribute with a single line

```python
...
class DB(nu.Shape):
    hits = nustd.kv.IntRef.slot()

# any Nu op
op = DB.hits.set(DB.hits + 1)

# same op — teleport it to a worker
remote = nustd.cluster.Teleport(op, target="gpu-0")

app = nu.With(
    nustd.cluster.RayCluster(),
    body=remote,
)
...
```

Powered by [`Ray`](https://github.com/ray-project/ray).

### LLM calls

*One wire, N providers.* Ollama, OpenAI, OpenRouter, Groq, xAI — same call.

LLM chat as a Ref. Swap the model string, keep the code. Local models and hosted APIs meet at the same interface.

- Add intelligence to any Nu app
- 7 providers out of the box

```python
...
class Bot(nu.Service):
    chat = nustd.llm.ChatRef.method(temperature=0.7)

# ask the model
op = Bot.chat(prompt="one-line haiku about rust")

app = nu.With(
    nustd.llm.ollama(Bot, host="localhost", model="qwen2.5:7b"),
    body=op,
)
...
```

### And more

Nu is batteries-included and covers the common cases. In-memory state, proxy, HTTP, Python objects, Claude Code, local parallelism — same model, same shape, same primitive as the four above.

→ [Explore all fabrics](https://nustack.dev/fabrics)

# 🏁 Quickstart

Install, run a demo, start hacking.

### 01 · Install

Python 3.10+ &middot; everything ships in the wheel.

```bash
pip install nucore "nustd[all]" nucli
```

### 02 · Run a demo

Each one boots a live browser dashboard and picks up where it left off on restart. `nu demo` lists them all.

| counter | sampled |
| :--- | :--- |
| ![counter demo](https://github.com/user-attachments/assets/fbeb4ea6-a2cc-4bb8-8bd6-35d05ec3fcc9) A live counter, persistent across restarts. <br> `nu demo counter` | ![sampled demo](https://github.com/user-attachments/assets/22e0ce72-47a2-47dd-9d2a-701645f10eea) An infinite series, live-sampled into a line-chart. <br> `nu demo sampled` |
| **movies** |   |
| ![movies demo](https://github.com/user-attachments/assets/8c67838d-d327-4866-996f-65999e3a05be) A movie tracker: form, filterable table, detail pages. <br> `nu demo movies` |   |

### 03 · Start hacking

- **[Read the docs](https://nustack.dev/docs)** — tutorials, how-tos, and the fabric reference.
- **[Browse examples](https://github.com/nustackdev/nu/tree/main/examples)** — full source for every demo, plus more programs to steal from.

# 🔋 Nu STD

Batteries included. 26 modules ship on top of the kernel.

Twelve are **fabrics**. Bind one and every Ref inside the bracket reaches a real system.

The rest re-surface Python's **standard library**. Call them anywhere, no binding. Same names, same call shape as the stdlib, except a call hands back a tree, not a value. So it composes into the rest of the program.

```bash
pip install "nustd[all]"      # every backend
pip install "nustd[kv,ui]"    # or one extra per fabric
```

| Module | What | Looks like |
| --- | --- | --- |
| [nustd.kv](https://nustack.dev/docs/reference/nustd/kv) | Persistent state. | `State.movies.append(m)` |
| [nustd.ui](https://nustack.dev/docs/reference/nustd/ui) | Reactive web UI. | `Dashboard.count.set_value(n)` |
| [nustd.cluster](https://nustack.dev/docs/reference/nustd/cluster) | Cluster compute. | `Teleport(Add(1,2), "gpu")` |
| [nustd.llm](https://nustack.dev/docs/reference/nustd/llm) | OpenAI-compatible chat. | `Bot.chat(prompt="…")` |
| [nustd.mem](https://nustack.dev/docs/reference/nustd/mem) | In-memory state. | `users.age.set(12)` |
| [nustd.proxy](https://nustack.dev/docs/reference/nustd/proxy) | Fabrics over the network. | `Proxy(Nav, "10.0.0.1")` |
| [nustd.http](https://nustack.dev/docs/reference/nustd/http) | Nu meets the web. | `Solana.get_slot()` |
| [nustd.service](https://nustack.dev/docs/reference/nustd/service) | Python objects as Refs. | `Calc.add(a=2, b=3)` |
| [nustd.cc](https://nustack.dev/docs/reference/nustd/cc) | Claude Code as a Ref. | `Agent.ask(prompt="…")` |
| [nustd.mp](https://nustack.dev/docs/reference/nustd/mp) | Local parallel execution. | `Teleport(Add(1,2), "worker")` |
| [nustd.mp_pool](https://nustack.dev/docs/reference/nustd/mp_pool) | A pool of workers, as a fabric. | `Teleport(body, worker=w)` |
| [nustd.ws_server](https://nustack.dev/docs/reference/nustd/ws_server) | Websockets, any wire protocol. | `SessionFor(conn, arm)` |
| [nustd.math](https://nustack.dev/docs/reference/nustd/math) | Math functions and constants. | `math.sqrt(2)` |
| [nustd.cmath](https://nustack.dev/docs/reference/nustd/cmath) | `complex` and its companions. | `cmath.polar(z)` |
| [nustd.random](https://nustack.dev/docs/reference/nustd/random) | The global RNG. | `random.randint(1, 6)` |
| [nustd.time](https://nustack.dev/docs/reference/nustd/time) | The process clock. | `time.monotonic()` |
| [nustd.datetime](https://nustack.dev/docs/reference/nustd/datetime) | Dates, times, deltas, timezones. | `datetime.date.today()` |
| [nustd.itertools](https://nustack.dev/docs/reference/nustd/itertools) | Iterator building blocks. | `itertools.product(a, b)` |
| [nustd.functools](https://nustack.dev/docs/reference/nustd/functools) | A fold over a stream. | `functools.reduce(Add, xs)` |
| [nustd.asyncio](https://nustack.dev/docs/reference/nustd/asyncio) | The non-blocking sleep. | `asyncio.sleep(1)` |
| [nustd.logging](https://nustack.dev/docs/reference/nustd/logging) | Loggers and level shortcuts. | `logging.getLogger(__name__)` |
| [nustd.pathlib](https://nustack.dev/docs/reference/nustd/pathlib) | Lexical path operations. | `pathlib.Path.of("a", "b")` |
| [nustd.uuid](https://nustack.dev/docs/reference/nustd/uuid) | UUIDs, all four versions. | `uuid.uuid4()` |
| [nustd.decimal](https://nustack.dev/docs/reference/nustd/decimal) | Exact decimal arithmetic. | `Decimal.of("0.1")` |
| [nustd.fractions](https://nustack.dev/docs/reference/nustd/fractions) | Exact rational arithmetic. | `Fraction.of(1, 3)` |
| [nustd.fin](https://nustack.dev/docs/reference/nustd/fin) | Nu's own financial types. | `Percentage.of(75.5)` |

# 📦 Apps built on Nu

End-user tools written as Nu programs.

| Repo | What |
| --- | --- |
| [nustackdev/nulog](https://github.com/nustackdev/nulog) | Pure-Python, serverless logger and metrics store. Log and observe metrics from any Python code; entries persist to an embedded KV store and scale to billions, in-process. One line boots a live viewer. |
| [nustackdev/nuagent](https://github.com/nustackdev/nuagent) | An AI agent that speaks Nu. The model answers with a program, not a tool call, so one turn reads, branches, loops and writes across real state. |
| [nustackdev/nuspace](https://github.com/nustackdev/nuspace) | Nu runtime built on Nu, self-hosted. |

# 📐 Spec

Nu is a reference implementation of the interaction model — a language-agnostic specification of what an interaction is, how Refs name locations, and how Interactions compose into programs.

[nustackdev/interaction-model](https://github.com/nustackdev/interaction-model)

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
