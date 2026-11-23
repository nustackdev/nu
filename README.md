<div align="center">
  <img width="112" alt="nu" src="https://nustack.dev/brand/logo-square-512@2x.png" />
  <h1>nu</h1>
  <p>The interaction primitive.</p>

  [![Python](https://img.shields.io/badge/python-%3E%3D%203.10-blue)](https://pypi.org/project/nucore/)
  [![PyPI](https://img.shields.io/pypi/v/nucore?color=yellow)](https://pypi.org/project/nucore/)
  [![Downloads](https://img.shields.io/pypi/dw/nucore?color=green)](https://pypi.org/project/nucore/)
  [![License](https://img.shields.io/badge/license-Apache%202.0-orange.svg)](LICENSE.md)

  [![Discord](https://img.shields.io/badge/discord-join-5865F2?logo=discord&logoColor=white)](https://discord.gg/tCa8YE7XVr)
  [![X](https://img.shields.io/twitter/follow/nustackdev?style=social)](https://x.com/nustackdev)

  [About](#about) · [Examples](#examples) · [Install](#install) · [Docs](https://nustack.dev/docs/nu) · [Tutorial](https://nustack.dev/docs/nu/tutorials/your-first-app)

</div>

nu is a Python programming model for apps that span many systems. Every resource is a Ref, wherever it lives: a database row, a UI widget, an LLM endpoint, a remote worker. Interactions with Refs are first-class primitives you compose into programs.

## About

Most app code is not about values, it is about moving them between systems: a database, a browser, a worker, an LLM. nu makes that interaction the primitive.

- **Ref**: a name for a value, wherever it lives. A KV slot, a text block in the browser, an LLM endpoint.
- **Interaction**: what you do with a Ref. Read, write, branch, iterate, compose.
- **Fabric**: binds Refs to a real system. Bind as many as you need, they all speak the same primitive.

Setting a text block in the browser is the same interaction as setting a KV slot.

## Examples

A counter that survives restarts:

```python
import nu
import nustd


class DB(nu.Shape):
    hits = nustd.kv.IntRef.slot()


op = DB.hits.init(0) >> DB.hits.inc() >> nu.print(nu.str(DB.hits))

app = nu.With(
    nustd.kv.rocksdb_navigator(".db"),
    body=nustd.kv.auto_flow_atomic(op),
)

nu.run(app)  # 1, then 2 on the next run, then 3
```

A live browser UI, same shape. Set the text block like a variable and the page updates:

```python
import asyncio

import nu
import nustd


class Home(nustd.ui.Column):
    hello = nustd.ui.TextRef.slot()


op = Home.hello.set("Hello, browser.")

asyncio.run(nu.arun(nustd.ui.serve(op)))
```

The same goes for workers, a Ray cluster or an LLM: bind another fabric, keep the code. More in [`examples/`](examples), eg `python examples/movies.py` for a form, a filterable table and detail pages.

## Install

Python 3.10 or newer.

```bash
pip install "nustd[all]"
```

`nucore` is the kernel: the model, the engine and in-memory state. [`nustd`](pkgs/nustd) adds the fabrics and pulls in `nucore`. Pick extras to install only what you need, eg `nustd[kv,ui]`.

| Module | What it binds | Extra |
| --- | --- | --- |
| [`nustd.kv`](https://nustack.dev/docs/nustd/reference/kv) | Persistent state over RocksDB, LMDB or SQLite, with transactions and change notifications | `kv` |
| `nustd.blob` | Write-once bytes, stored and streamed by range. On LMDB, plain files or S3 | `blob` |
| [`nustd.ui`](https://nustack.dev/docs/nustd/reference/ui) | Widgets as Refs, rendered in the browser and kept live | `ui` |
| [`nustd.mp`](https://nustack.dev/docs/nustd/reference/mp), [`nustd.cluster`](https://nustack.dev/docs/nustd/reference/cluster) | Local worker processes or a Ray cluster: run any tree on any worker | `mp`, `cluster` |
| [`nustd.proxy`](https://nustack.dev/docs/nustd/reference/proxy) | Any fabric, used from another process | `proxy` |
| `nustd.acp` | Coding agents (Claude Code, Codex, Gemini) over the Agent Client Protocol | `acp` |
| [`nustd.llm`](https://nustack.dev/docs/nustd/reference/llm) | OpenAI-compatible chat: OpenAI, Ollama, vLLM, OpenRouter, Groq, xAI, Cerebras | `llm` |

Plus Python's standard library in the same shape: `math`, `random`, `time`, `datetime`, `itertools`, `functools`, `json`, `pathlib`, `uuid`, `decimal` and more. Same names and call signatures, but a call returns a tree that composes into the rest of the program. Every module in the [nustd README](pkgs/nustd).

## The stack

nu is the Python implementation of the [interaction model](https://github.com/nustackdev/interaction-model). [nuspace](https://github.com/nustackdev/nuspace) is what we build with it: a computational space where everything, the space included, is a nu program.

## Community

- [Discord](https://discord.gg/tCa8YE7XVr): ask questions, share what you build with nu
- [X @nustackdev](https://x.com/nustackdev): releases and work in progress
- [Issues](https://github.com/nustackdev/nu/issues): bugs and feature requests

Building on nu? Add the badge:

[![nu](https://img.shields.io/badge/built%20with-nu-%237A4CE0)](https://github.com/nustackdev/nu)

```md
[![nu](https://img.shields.io/badge/built%20with-nu-%237A4CE0)](https://github.com/nustackdev/nu)
```

## License

Apache-2.0. See [LICENSE.md](LICENSE.md).
