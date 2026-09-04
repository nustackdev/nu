# nustd

Batteries for [Nu](https://github.com/nustackdev/nu).

`nucore` is the kernel: the language, the engine, the core atoms, flows,
spans, forms, the tree rewrites, `nu.prog`, `nu.inspect`. It has no
fabric backends in it. The `nu` command lives in `nucli`.

`nustd` is everything that talks to the outside world. It installs into the
same `nu.` namespace, so nothing about how you import changes:

| Fabric        | Extra                | What it is                            |
| ------------- | -------------------- | ------------------------------------- |
| `nu.std`      | -                    | Nu bindings for the Python stdlib      |
| `nu.service`  | -                    | Service / method dispatch              |
| `nu.mem`      | `nustd[mem]`         | In-process refs                        |
| `nu.kv`       | `nustd[kv]`          | Key-value storage (virtuals, RocksDB)  |
| `nu.ui`       | `nustd[ui]`          | The nudle web UI runtime               |
| `nu.llm`      | `nustd[llm]`         | LLM calls                              |
| `nu.cc`       | `nustd[cc]`          | Claude Agent SDK sessions              |
| `nu.http`     | `nustd[http]`        | HTTP client atoms                      |
| `nu.proxy`    | `nustd[proxy]`       | Remote objects over invisibles         |
| `nu.mp`       | `nustd[mp]`          | Multiprocessing workers                |
| `nu.cluster`  | `nustd[cluster]`     | Ray                                    |

## Install

```bash
pip install nustd[all]      # everything
pip install nustd[kv,ui]    # just what you need
```

`nucore` comes along as a dependency. Add `nucli` for the `nu` command:
`pip install "nustd[all]" nucli`.

Released in lockstep with `nucore` and `nucli`. Docs at
[nustack.dev](https://nustack.dev).
