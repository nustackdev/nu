# nustd

Batteries for [Nu](https://github.com/nustackdev/nu).

`nucore` is the kernel: the language, the engine, the core atoms, flows,
spans, forms, the tree rewrites, `nu.prog`, `nu.inspect`. It has no
fabric backends in it. The `nu` command lives in `nucli`.

`nustd` is everything that talks to the outside world. One import, then
dot-access: `import nustd`, then `nustd.kv`, `nustd.ui`, `nustd.uuid`.

| Fabric          | Extra            | What it is                            |
| --------------- | ---------------- | ------------------------------------- |
| `nustd.service` | -                | Service / method dispatch             |
| `nustd.mem`     | `nustd[mem]`     | In-process refs                       |
| `nustd.kv`      | `nustd[kv]`      | Key-value storage (virtuals, RocksDB) |
| `nustd.ui`      | `nustd[ui]`      | The nudle web UI runtime              |
| `nustd.llm`     | `nustd[llm]`     | LLM calls                             |
| `nustd.cc`      | `nustd[cc]`      | Claude Agent SDK sessions             |
| `nustd.http`    | `nustd[http]`    | HTTP client atoms                     |
| `nustd.proxy`   | `nustd[proxy]`   | Remote objects over invisibles        |
| `nustd.mp`      | `nustd[mp]`      | Multiprocessing workers               |
| `nustd.cluster` | `nustd[cluster]` | Ray                                   |

The standard library sits at the same level, one module per Python stdlib
module it mirrors: `nustd.uuid`, `nustd.datetime`, `nustd.decimal`,
`nustd.math`, `nustd.pathlib`, `nustd.logging`, `nustd.fin` and the rest. No
extra needed, they are pure Nu.

## Install

```bash
pip install nustd[all]      # everything
pip install nustd[kv,ui]    # just what you need
```

`nucore` comes along as a dependency. Add `nucli` for the `nu` command:
`pip install "nustd[all]" nucli`.

Released in lockstep with `nucore` and `nucli`. Docs at
[nustack.dev](https://nustack.dev).
