# nucli

The `nu` command line for [Nu](https://nustack.dev).

Installing this gives you the `nu` executable:

```bash
nu --version
nu doctor          # environment + fabric backend check
nu demo movies     # run a packaged demo app
nu telemetry       # see / change telemetry settings
```

It imports as `nucli`, installs the `nu` command, and depends on
[`nustd`](https://pypi.org/project/nustd/) (which pulls the
[`nucore`](https://pypi.org/project/nucore/) kernel) because the
packaged demos run on `nustd.ui` and `nustd.kv` at runtime.

You normally do not install this directly - `pip install "nustd[all]" nucli`
brings it along. Released in lockstep with the kernel. Docs at
[nustack.dev](https://nustack.dev).
