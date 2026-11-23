<div align="center">
  <img width="112" alt="nustd" src="https://nustack.dev/brand/logo-square-512@2x.png" />
  <h1>nustd</h1>
  <p>The nu standard library.</p>

  [![Python](https://img.shields.io/badge/python-%3E%3D%203.10-blue)](https://pypi.org/project/nustd/)
  [![PyPI](https://img.shields.io/pypi/v/nustd?color=yellow)](https://pypi.org/project/nustd/)
  [![Downloads](https://img.shields.io/pypi/dw/nustd?color=green)](https://pypi.org/project/nustd/)
  [![License](https://img.shields.io/badge/license-Apache%202.0-orange.svg)](https://github.com/nustackdev/nu/blob/main/LICENSE.md)

  [![Discord](https://img.shields.io/badge/discord-join-5865F2?logo=discord&logoColor=white)](https://discord.gg/tCa8YE7XVr)
  [![X](https://img.shields.io/twitter/follow/nustackdev?style=social)](https://x.com/nustackdev)

  [Fabrics](#fabrics) · [Standard library](#standard-library) · [Install](#install) · [Reference](https://nustack.dev/docs/nustd) · [nu](https://github.com/nustackdev/nu)

</div>

Batteries for [nu](https://github.com/nustackdev/nu): storage, UI, workers and more, ready to use.

`nucore` is the kernel: the model, the engine, flows, forms, tree rewrites and `nu.mem`, the in-memory fabric over plain dicts. Everything that talks to the outside world lives here. One import, then dot-access: `import nustd`, then `nustd.kv`, `nustd.ui`, `nustd.uuid`.

## Fabrics

A fabric binds Refs to a real system. Bind one and every Ref inside the bracket reaches it.

| Module | What it is | Extra |
| --- | --- | --- |
| [`nustd.kv`](https://nustack.dev/docs/nustd/reference/kv) | Persistent state over RocksDB, LMDB or SQLite. Transactions, snapshots and change notifications, built in | `kv` |
| `nustd.blob` | Write-once bytes under an id, stored and streamed by range. On LMDB, plain files or any S3-compatible store | `blob`, `blob_s3` |
| `nustd.fs` | A real directory mounted for the span of a tree. Every path stays inside the mount. Atomic writes, file locks across processes | - |
| [`nustd.ui`](https://nustack.dev/docs/nustd/reference/ui) | Widgets as Refs: text, buttons, tables. Rendered in the browser and live-updated as your state changes | `ui` |
| [`nustd.mp`](https://nustack.dev/docs/nustd/reference/mp) | A pool of local worker processes. Launch workers and run nu trees on them | `mp` |
| [`nustd.cluster`](https://nustack.dev/docs/nustd/reference/cluster) | Teleport a nu tree to any worker in your Ray cluster. It runs there and returns the result | `cluster` |
| [`nustd.proxy`](https://nustack.dev/docs/nustd/reference/proxy) | Puts other fabrics on the network. Bind one in a process, use it from another over TCP or a unix socket | `proxy` |
| [`nustd.llm`](https://nustack.dev/docs/nustd/reference/llm) | OpenAI-compatible chat and streaming, one wire for OpenAI, Ollama, vLLM, OpenRouter, Groq, xAI and Cerebras | `llm` |
| `nustd.acp` | Drives coding agents (Claude Code, Codex, Gemini, OpenCode) over the Agent Client Protocol. Agents and sessions are Refs | `acp` |
| [`nustd.http`](https://nustack.dev/docs/nustd/reference/http) | HTTP endpoints declared as Refs, called through an httpx client | `http` |
| [`nustd.service`](https://nustack.dev/docs/nustd/reference/service) | Exposes a Python object as a nu service: its methods become Refs | - |
| [`nustd.queue`](https://nustack.dev/docs/nustd/reference/queue) | A bounded queue between the event loop and threads | `queue` |
| [`nustd.ws_server`](https://nustack.dev/docs/nustd/reference/ws_server) | Serves websocket connections. It owns the connection lifecycle, the session class owns the protocol | `ws_server` |
| [`nustd.valkey`](https://nustack.dev/docs/nustd/reference/valkey) | Runs a private Valkey server, bundled, on a unix socket for the span of a tree. kv uses it for change notifications across processes | `valkey` |
| `nustd.webbrowser` | Opens a browser tab on a url once a server there answers | - |

## Standard library

Python's standard library, as nu. One module per stdlib module it mirrors, same names and call shape, except a call returns a tree that composes into the rest of the program: `math`, `cmath`, `random`, `time`, `datetime`, `itertools`, `functools`, `asyncio`, `logging`, `json`, `pathlib`, `uuid`, `decimal`, `fractions`. Plus `fin`, nu's own financial value types. No extra needed.

A library whose values can sit in a slot carries the leaves for them, one submodule per fabric: `nustd.decimal.mem.DecimalRef` for `nu.mem`, `nustd.decimal.kv.DecimalRef` for `nustd.kv`.

## Install

Python 3.10 or newer.

```bash
pip install "nustd[all]"     # everything
pip install "nustd[kv,ui]"   # just what you need
```

`nucore` comes along as a dependency. Released in lockstep with it.

## License

Apache-2.0. See [LICENSE.md](https://github.com/nustackdev/nu/blob/main/LICENSE.md).
