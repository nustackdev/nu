# nucore

The kernel of [Nu](https://nustack.dev) - the interaction primitive. Build apps
in one primitive that spans your whole stack.

This distribution is the language and the engine, nothing else: `nu.lang`,
`nu.engine`, `nu.core`, `nu.flows`, `nu.spans`, `nu.forms`, `nu.tree`,
`nu.factory`, `nu.context`, `nu.domains`, `nu.prog`, `nu.info`, `nu.inspect`,
`nu.reactive`. No fabric backend ever lands here, and it depends on nothing but
`typing-extensions` and `cloudpickle`.

The rest of the stack merges into the same `nu.` namespace:

- [`nustd`](https://pypi.org/project/nustd/) - the fabrics (`nu.kv`, `nu.ui`,
  `nu.mem`, `nu.llm`, `nu.http`, `nu.cluster`, ...)
- [`nucli`](https://pypi.org/project/nucli/) - the `nu` command

```bash
pip install "nustd[all]" nucli   # kernel + all fabrics + the CLI
pip install nucore               # kernel alone
nu demo movies
```

All three ship in lockstep. Docs at [nustack.dev](https://nustack.dev).
