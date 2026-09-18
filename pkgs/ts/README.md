# pkgs/ts

The TypeScript half of [Nu](https://nustack.dev). One npm workspace, three
packages.

| Directory | Published as                 | What                                                              |
| --------- | ---------------------------- | ----------------------------------------------------------------- |
| `ui-core` | `@nustackdev/ui-core` (npm)  | Wire protocol and tree store. No React.                            |
| `ui-kit`  | `@nustackdev/ui-kit` (npm)   | Design kit: tokens, primitives, node types, tree bindings.         |
| `nudle`   | not published to npm         | The nudle SPA. Its vite output ships as the `nudle` wheel from `pkgs/nudle`. |

Both npm packages ship source-only, no dist bundle, so consumers compile the
TypeScript and Tailwind themselves. That is how `nuspace` picks them up
straight from the registry.

## Working here

```bash
make web-install    # npm install across the workspace
make web-dev        # vite dev server, HMR, ws proxy to :8080
make web-build      # build the SPA into nudle/dist
```

Or from this directory:

```bash
npm run typecheck   # tsc --noEmit across all three
npm run check       # biome
```

One workspace on purpose, so `react` hoists to a single copy. Keep it that
way: the kit pulls react through its own dependency graph, and a second copy
makes every hook in a kit component throw. `nuspace` consumes these from the
registry instead and has to alias react by absolute path to dodge exactly
that.

## Releasing

See [RELEASING.md](RELEASING.md). Tag-based, one workflow per package, and
`@nustackdev/ui-core` publishes first when both bump.
