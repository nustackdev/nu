---
title: Card
---

Card-styled box wrapping child slots. Optional title, subtitle, and footer
strings on the Section. `CardRef` is a Shape (Section), not a Ref.
Display-only, server-owned.

## kind

section (layout primitive)

## defaults (class-level)

| field | type | default | notes |
| --- | --- | --- | --- |
| `title` | `str` | `""` | header line. empty hides the header region. |
| `subtitle` | `str` | `""` | smaller line under the title. empty hides the subtitle. |
| `footer` | `str` | `""` | plain text footer. empty hides the footer region and its top border. |

Children declared as ordinary slots stack vertically in the body region
with a small gap. v1 has no separate header or footer slots; the three
strings are the entire header and footer surface.

## interactions

| op | dir | payload | nu method | notes |
| --- | --- | --- | --- | --- |
| `store_title` | server -> tab | `str` | `store_title` | nil coerces to `""`; hides header when both title and subtitle are empty. |
| `store_subtitle` | server -> tab | `str` | `store_subtitle` | nil coerces to `""`. |
| `store_footer` | server -> tab | `str` | `store_footer` | nil coerces to `""`; empty hides the footer block and its top border. |

No tab -> server traffic. Card is display-only.

## wire payloads

```
// mount field entry, recursive
{
  "path": "HomePage.hero",
  "type": "CardRef",
  "props": {"title": "Stats", "subtitle": "last 24h", "footer": ""},
  "fields": [
    {"path": "HomePage.hero.count", "type": "StatRef", "props": {...}},
    {"path": "HomePage.hero.note",  "type": "TextRef", "props": {...}}
  ]
}

// runtime updates
{"op": "store_title",    "ref": "HomePage.hero", "payload": "Stats (live)"}
{"op": "store_subtitle", "ref": "HomePage.hero", "payload": "last 24h"}
{"op": "store_footer",   "ref": "HomePage.hero", "payload": "updated 12s ago"}
```

Example:

```python
class Hero(nudle.CardRef):
    title = "Stats"
    subtitle = "last 24h"
    footer = ""

    count = nudle.StatRef.slot()
    note  = nudle.TextRef.slot()


class HomePage(nudle.Page):
    hero = Hero.slot()


# server-side updates
Hero.store_title("Stats (live)")
Hero.store_footer("updated 12s ago")
```

The `store_*` classmethods return Nu commands; pipe them through the Nu
runtime like any other interaction. They resolve the section's wire path
from `_nudle_mount` at run time.

## renderer

`web/src/refs/card.tsx`. A `<section>` styled like a shadcn card
(`rounded-md border bg-card text-card-foreground shadow-sm`) with three
regions: an optional `<header>` (title + subtitle), a `<div>` body with
`flex flex-col gap-3` for children, and an optional `<footer>` with a
top border. Each child path is resolved against the global slice table
and dispatched through the shared `renderers` map wrapped in
`ErrorBoundary`. Missing slice or missing renderer prints a small
destructive-colored line and continues.

## slice shape

```
{
  type: "CardRef",
  value: null,
  title: string,
  subtitle: string,
  footer: string,
  children: string[],
  store_title:    (v: string | null) => void,
  store_subtitle: (v: string | null) => void,
  store_footer:   (v: string | null) => void,
}
```

Server-owned. Seeded from `field.props` and the nested `fields` list on
mount. Each `store_*` handler coerces nil to `""` and writes the matching
slice field.

## edge cases

- both `title == ""` and `subtitle == ""`: the entire `<header>` is omitted.
- `footer == ""`: the `<footer>` and its top border are omitted.
- nil payload to any `store_*` op: stored as `""`; the corresponding region hides on next render.
- non-string payload: coerced via `String(v)`.
- empty `children` list: body `<div>` renders empty (still padded).
- child slice missing from the registry: skipped with a small inline error line; siblings render normally.
- nested CardRef as a child: supported; the mount walker recurses through Section entries identically.

## non-goals

- no rich content in title / subtitle / footer (no markdown, no inline Refs, no react nodes).
- no separate header or footer child slots in v1.
- no variant / padding / border / shadow knobs (use Container if you need chrome tuning).
- no actions row, no card-level click handler, no notify / read.
- no collapsing or expand toggle (Accordion's job).
- no per-child overrides.
