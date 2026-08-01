# Releasing UI packages

Two npm packages ship from this workspace: `@nustackdev/ui-core` and `@nustackdev/ui-kit`. Everything is automated through GitHub Actions.

## One-time setup

1. Create a **granular npm access token** at https://npmjs.com/settings/<you>/tokens/granular:
   - Scope: only `@nustackdev/*`
   - Permission: `Read and write`
   - Expiration: pick a horizon (a year is fine, calendar it)
   - **Enable "Bypass 2FA"** so CI can publish unattended.
2. Add the token as GitHub repo secret `NPM_TOKEN` at https://github.com/nustackdev/nu/settings/secrets/actions.
3. That's it. Publish workflows are in `.github/workflows/`.

## Publishing

Tag-based, one workflow per package.

**`@nustackdev/ui-core`** — `.github/workflows/publish-ui-core.yml`, triggers on tag `ui-core@X.Y.Z`.

**`@nustackdev/ui-kit`** — `.github/workflows/publish-ui-kit.yml`, triggers on tag `ui-kit@X.Y.Z`.

### Release steps

```bash
# 1. Bump the version in the target package.json
$EDITOR src/nu/ui/core/package.json   # or kit/package.json

# 2. Commit the bump
git add src/nu/ui/core/package.json
git commit -m "Bump ui-core to 0.2.0"
git push

# 3. Tag from that commit and push the tag
git tag ui-core@0.2.0
git push origin ui-core@0.2.0
```

The workflow validates that the tag version matches `package.json`, publishes to npm, and the package shows up on npmjs.com in a minute or two.

**Provenance is off** because the repo is private and we're on the free npm tier (provenance requires a public repo or paid Enterprise plan). If the repo becomes public later, add `--provenance` back to the publish step in both `publish-ui-*.yml` files and add `id-token: write` is already set at the job level.

**Order matters when both packages bump:** publish `@nustackdev/ui-core` first, wait for it to appear on the registry, then publish `@nustackdev/ui-kit`. Kit's `package.json` depends on core; if kit is published before the new core is available, installs will resolve stale.

### Manual dispatch

Both publish workflows also expose `workflow_dispatch`. Go to Actions in GitHub, pick the workflow, click "Run workflow" against `main`. Skips the tag-verification step, so use with care. Useful for re-publishing after transient npm errors.

## What ships

Both packages ship **source-only** (no dist bundle). Consumers with TypeScript + Tailwind pick them up directly:

- `@nustackdev/ui-core` — `src/**` including `protocol.ts`
- `@nustackdev/ui-kit` — `src/**` including `index.css`, `components/ui/*`, `refs/*`, `store.ts`

Fonts (Inter, JetBrains Mono WOFF2) ship inside the kit tarball because `index.css` `@font-face`-references them at relative paths.

## Version scheme

Both packages are `0.x.y` while the design system is still shaping. Bump patch (`0.y.z+1`) for compatible fixes, minor (`0.y+1.0`) for additions, prerelease tags like `0.2.0-alpha.0` for previews.

## Troubleshooting

- **"tag ui-core@X.Y.Z does not match core/package.json"** — the guardrail rejected the publish because the tag string and the package.json version disagree. Either fix the tag or the version and try again.
- **"npm ERR! 402 Payment Required"** — the package name is scoped and needs `--access public`. The workflow passes that already, so if you see this locally, add the flag by hand.
- **"npm ERR! Cannot publish over the previously published versions"** — you're trying to reuse a version. Bump.
