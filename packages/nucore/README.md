# nucore

The kernel of [Nu](https://nustack.dev) - the interaction primitive. Build apps
in one primitive that spans your whole stack.

This distribution is the language and the engine, nothing else: `nu.lang`,
`nu.engine`, `nu.core` (with `nu.core.flows`, `nu.core.spans`,
`nu.core.reactive`), `nu.forms`, `nu.tree`, `nu.factory`, `nu.context`,
`nu.domains`, `nu.prog`, `nu.inspect`. No fabric backend ever lands here, and it
depends on nothing but `typing-extensions` and `cloudpickle`.

The rest of the stack sits beside it, one import name each:

- [`nustd`](https://pypi.org/project/nustd/) - the fabrics (`nustd.kv`, `nustd.ui`,
  `nustd.mem`, `nustd.llm`, `nustd.http`, `nustd.cluster`, ...)
- [`nucli`](https://pypi.org/project/nucli/) - the `nu` command

```bash
pip install "nustd[all]" nucli   # kernel + all fabrics + the CLI
pip install nucore               # kernel alone
nu demo movies
```

All three ship in lockstep. Docs at [nustack.dev](https://nustack.dev).
