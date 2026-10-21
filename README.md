<div align="center">
  <img width="128" alt="Nu" src="https://nustack.dev/brand/logo-square-512@2x.png" />
  <h1>
    nu – the interaction primitive
  </h1>
  <p></p>Build apps in one primitive that spans your whole stack — databases, UIs, AI agents, and services.</p>

  [![PyPI - Python Version](https://img.shields.io/badge/python-%3E%3D%203.10-blue)](https://pypi.org/project/nucore/)
  [![PyPI Package](https://img.shields.io/pypi/v/nucore?color=yellow)](https://pypi.org/project/nucore/)
  [![PyPI Downloads](https://img.shields.io/pypi/dw/nucore?color=green)](https://pypi.org/project/nucore/)
  [![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
  
  [![Discord](https://img.shields.io/badge/discord-join-5865F2?logo=discord&logoColor=white)](https://discord.gg/tCa8YE7XVr)
  [![Twitter Follow](https://img.shields.io/twitter/follow/nustackdev?style=social)](https://twitter.com/nustackdev)
</div>

## About

A tiny script keeps its values in memory and calls functions on them. Real apps don't stay there. Values live in a database, arrive from a browser form, render into a dashboard, get recomputed by a background job. Almost none of the code is about the values anymore — it's all interaction between systems.

Nu makes interaction the primitive.

- **Ref**: a name for a value, wherever it lives. A KV slot, a text block in the browser, an LLM endpoint, a remote object.
- **Interaction**: what you do with a Ref. Read, write, branch, iterate, compose.
- **Fabric**: binds Refs to a real system. Bind as many as you need, they all speak the same primitive.

> **Same primitive, different system.** One Ref for any resource, one Interaction for any op. Setting a browser text block is the same interaction as setting a KV slot.

Nu is the Python implementation of the [interaction model](https://github.com/nustackdev/interaction-model).

## Build with Nu

Four fabrics from [nustd](pkgs/nustd), the same code shape in each.

### Persistent state

*Persistent state. Stores any Python type.*

Reach any value by name; it survives restarts. Same code local or sharded across a cluster.

- Serverless, scales to terabytes
- Store any Python type

```python
import nu
import nustd


class DB(nu.Shape):
    hits = nustd.kv.IntRef.slot()


# +1 to a persistent counter, starting at 0
op = DB.hits.init(0) >> DB.hits.inc() >> nu.print(nu.str(DB.hits))

app = nu.With(
    nustd.kv.rocksdb_navigator(".db"),
    body=nustd.kv.auto_flow_atomic(op),
)

nu.run(app)  # 1, then 2 on the next run, then 3
```

Powered by [`virtuals`](https://github.com/nustackdev/virtuals) · [`rdbpy`](https://github.com/nustackdev/rdbpy) · [`RocksDB`](https://github.com/facebook/rocksdb) · [`LMDB`](https://www.symas.com/lmdb).

### Live browser UIs

*Reactive UIs from Python.* No JS, no build step, no websocket you had to write.

A text block, a chart, a form — set them like variables, they render. Update the value, the browser updates itself.

- 50+ components out of the box
- Live updates for free

```python
import asyncio

import nu
import nustd


class Home(nustd.ui.Page):
    hello = nustd.ui.TextRef.slot()


# renders live in the browser
op = Home.hello.set("Hello, browser.")

asyncio.run(nu.arun(nustd.ui.serve(Home, op)))
```

Powered by [`React`](https://react.dev) · [`Zustand`](https://github.com/pmndrs/zustand).

### Distributed execution

*Same code runs local or across the cluster.* No worker pool to run.

Teleport any Nu tree to any worker; it runs there and returns the result. Where it runs is a binding, not a rewrite.

- Same code, local or remote
- Distribute with a single line

```python
import asyncio

import nu
from nustd.cluster import RayCluster, RayService, Teleport

# any Nu tree
op = nu.print("hello from a worker")

# a local ray instance with two workers; "auto" joins your cluster instead
app = nu.Provide(RayCluster, {"address": None},
    nu.ProvideList(RayService, [{"num_cpus": 1}, {"num_cpus": 1}],
        nu.Parallel(
            Teleport(op, target=0),
            Teleport(op, target=1),
        ),
    ),
)

asyncio.run(nu.arun(app))
```

Powered by [Ray](https://github.com/ray-project/ray). For local processes, `nustd.mp` and `nustd.mp_pool` take the same shape.

### LLM calls

*One wire, N providers.* Ollama, OpenAI, OpenRouter, Groq, xAI — same call.

LLM chat as a Ref. Swap the model string, keep the code. Local models and hosted APIs meet at the same interface.

- Add intelligence to any Nu app
- 7 providers out of the box

```python
import nu
import nustd


class Bot(nu.Service):
    chat = nustd.llm.ChatRef.method(temperature=0.7)


# ask the model
op = Bot.chat(prompt="one-line haiku about rust")

app = nu.With(
    nustd.llm.ollama(Bot, host="localhost", model="qwen2.5:7b"),
    body=nu.print(nu.str(nu.dict(op)["text"])),
)

nu.run(app)
```

### And more

HTTP, remote fabrics over the network, Python objects as Refs, Claude Code sessions, local worker pools, websocket servers. Same model, same shape. See [all of nustd](#nustd).

## Quickstart

### Install

Python 3.10 or newer.

```bash
pip install "nustd[all]"
```

`nustd` pulls in `nucore`, the kernel. `[all]` adds every backend.

### Run an example

Run one from [`examples/`](examples).

- A live counter, persistent across restarts `python examples/counter.py`
- An infinite series, live-sampled into a line chart `python examples/sampled.py`
- A movie tracker: form, filterable table, detail pages `python examples/movies.py`

### Next

- [Your first app](https://nustack.dev/docs/nu/tutorials/your-first-app): a tutorial from a counter to a live page.
- [Docs](https://nustack.dev/docs/nu): tutorials, how-tos and the full reference.
- [Examples](examples): every demo above, plus more programs to take from.

## Nu STD

The kernel, `nucore`, holds the language, the engine and one fabric of its own: `nu.mem`, in-memory state over plain dicts. Everything that talks to the outside world lives in [nustd](pkgs/nustd).

Fabrics. Bind one and every Ref inside the bracket reaches a real system.

| Module | What | Extra |
| --- | --- | --- |
| [`nustd.kv`](https://nustack.dev/docs/nustd/reference/kv) | Persistent state over RocksDB, LMDB or SQLite | `kv` |
| [`nustd.ui`](https://nustack.dev/docs/nustd/reference/ui) | Live web UI | `ui` |
| [`nustd.cluster`](https://nustack.dev/docs/nustd/reference/cluster) | Run trees across a Ray cluster | `cluster` |
| [`nustd.mp`](https://nustack.dev/docs/nustd/reference/mp) / [`mp_pool`](https://nustack.dev/docs/nustd/reference/mp_pool) | Run trees in local worker processes | `mp` |
| [`nustd.llm`](https://nustack.dev/docs/nustd/reference/llm) | OpenAI-compatible chat, seven providers | `llm` |
| [`nustd.cc`](https://nustack.dev/docs/nustd/reference/cc) | Claude Code sessions as Refs | `cc` |
| [`nustd.http`](https://nustack.dev/docs/nustd/reference/http) | HTTP calls | `http` |
| [`nustd.proxy`](https://nustack.dev/docs/nustd/reference/proxy) | Any fabric, used from another process | `proxy` |
| [`nustd.service`](https://nustack.dev/docs/nustd/reference/service) | Python objects as Refs | - |
| [`nustd.queue`](https://nustack.dev/docs/nustd/reference/queue) | A queue between the event loop and threads | `queue` |
| [`nustd.ws_server`](https://nustack.dev/docs/nustd/reference/ws_server) | A websocket host | `ws_server` |
| [`nustd.valkey`](https://nustack.dev/docs/nustd/reference/valkey) | A private Valkey server, for change notifications across processes | `valkey` |

The standard library. Python's stdlib, same names and call shape, except a call returns a tree that composes into the rest of the program: `math`, `cmath`, `random`, `time`, `datetime`, `itertools`, `functools`, `asyncio`, `logging`, `pathlib`, `uuid`, `decimal`, `fractions`, plus Nu's own `fin`. No extra needed.

```bash
pip install "nustd[all]"     # everything
pip install "nustd[kv,ui]"   # just what you need
```

Full list in the [nustd README](pkgs/nustd) and the [reference](https://nustack.dev/docs/nustd).

## Spec

Nu implements the [interaction model](https://github.com/nustackdev/interaction-model), a language-agnostic specification of what an interaction is, how Refs name locations and how Interactions compose into programs.

## Community

- [Discord](https://discord.gg/tCa8YE7XVr) for questions and what you build
- [X @nustackdev](https://x.com/nustackdev) for releases and demos
- [Issues](https://github.com/nustackdev/nu/issues) for bugs and feature requests

Building on Nu? Add the badge to your README:

[![Nu](https://img.shields.io/badge/built%20with-Nu-%237A4CE0)](https://github.com/nustackdev/nu)

```
[![Nu](https://img.shields.io/badge/built%20with-Nu-%237A4CE0)](https://github.com/nustackdev/nu)
```

## License

Apache-2.0. See [LICENSE.md](LICENSE.md).
