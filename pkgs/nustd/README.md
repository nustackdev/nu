<div align="center">
  <img width="128" alt="nustd" src="https://nustack.dev/brand/logo-square-512@2x.png" />
  <h3>
    nustd – the Nu standard library
  </h3>
  Batteries for <a href="https://github.com/nustackdev/nu">Nu</a>: the fabrics that reach the outside world, and Python's stdlib as Nu.
</div>

<br/>

<div align="center">

  [![Discord](https://img.shields.io/badge/discord-join-5865F2?logo=discord&logoColor=white)](https://discord.gg/tCa8YE7XVr)
  [![Twitter Follow](https://img.shields.io/twitter/follow/nustackdev?style=social)](https://twitter.com/nustackdev)

  [![Platform Support](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-blue)]()
  [![PyPI - Python Version](https://img.shields.io/badge/python-%3E%3D%203.10-blue)](https://pypi.org/project/nustd/)
  [![PyPI Package](https://img.shields.io/pypi/v/nustd?color=yellow)](https://pypi.org/project/nustd/)
  [![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
  [![PyPI Downloads](https://img.shields.io/pypi/dw/nustd?color=green)](https://pypi.org/project/nustd/)

</div>

---

<h3 align="center">
  <a href="#ℹ️-about"><b>About</b></a> &bull;
  <a href="#install"><b>Install</b></a> &bull;
  <a href="https://nustack.dev/docs/nustd"><b>Reference</b></a> &bull;
  <a href="https://github.com/nustackdev/nu"><b>nu</b></a>
</h3>

---

# ℹ️ About

`nucore` is the kernel: the language, the engine, the core atoms, flows,
spans, forms, the tree rewrites, `nu.prog`, `nu.inspect`, and `nu.mem`, the
in-memory fabric over plain dicts. No other fabric lives in it.

`nustd` is everything that talks to the outside world. One import, then
dot-access: `import nustd`, then `nustd.kv`, `nustd.ui`, `nustd.uuid`.

| Fabric          | Extra            | What it is                            |
| --------------- | ---------------- | ------------------------------------- |
| `nustd.service` | -                | Service / method dispatch             |
| `nustd.queue`   | `nustd[queue]`   | Janus queue refs (loop and threads)   |
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

A library whose values can sit in a slot carries the leaves for them, one
submodule per fabric: `nustd.decimal.mem.DecimalRef` for `nu.mem`,
`nustd.decimal.kv.DecimalRef` for `nustd.kv`.

## Install

```bash
pip install nustd[all]      # everything
pip install nustd[kv,ui]    # just what you need
```

`nucore` comes along as a dependency.

Released in lockstep with `nucore`. Docs at
[nustack.dev](https://nustack.dev).
