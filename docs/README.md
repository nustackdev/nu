# nu docs

Nu website + docs. Fumadocs 16 · Next 16 · React 19 · Tailwind 4 · TS.

```bash
pnpm i && pnpm dev   # http://localhost:3000
```

## Layout

- `app/(home)` — landing
- `app/docs` — docs shell
- `content/docs` — MDX source (Catalogue, Guides, Nudle)
- `lib/source.ts` — content adapter · `lib/shared.ts` — app + git config
- `source.config.ts` — MDX + frontmatter schema
