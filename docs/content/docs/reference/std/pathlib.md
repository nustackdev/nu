---
title: nu.std.pathlib
---

Mirrors `pathlib` 1-1, backed by `PurePath` - only lexical path operations, no filesystem I/O (deferred: `exists`, `read_text`, `iterdir`, `glob`, ...).

`from nu.std.pathlib import Path`

| Name | Sort | Signature       | Effect | Meaning                                                                                             |
| ---- | ---- | ---------------- | ------ | ------------------------------------------------------------------------------------------------------ |
| Path | Form | `Path.of(*segments)` | pure | pure path; `cwd()`/`home()`, `.name`/`.stem`/`.suffix`/`.parts`/`.parent`/`.root`/`.anchor`/`.drive`, `with_name`/`with_stem`/`with_suffix`/`joinpath`/`relative_to`, `/` operator, `as_posix()`/`as_uri()`, `match()`/`is_absolute()`/`is_relative_to()`, comparison |
