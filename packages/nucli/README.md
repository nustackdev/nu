# nucli

The `nu` command line for [Nu](https://nustack.dev).

Installing this gives you the `nu` executable:

```bash
nu --version
nu doctor          # environment + fabric backend check
nu demo movies     # run a packaged demo app
nu telemetry       # see / change telemetry settings
```

It ships `nu._cli` into the `nu.` namespace and depends on
[`nustd`](https://pypi.org/project/nustd/) (which pulls the
[`nucore`](https://pypi.org/project/nucore/) kernel) because the
packaged demos run on `nu.ui` and `nu.kv` at runtime.

You normally do not install this directly - `pip install "nustd[all]" nucli`
brings it along. Released in lockstep with the kernel. Docs at
[nustack.dev](https://nustack.dev).
