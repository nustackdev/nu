# Row

Layout primitive. A `Row` is a Shape (Section), not a Ref. It arranges its
child slots horizontally with optional gap, alignment, justify, wrap, and
padding. Display-only, server-owned.

Subclass `nudle.Row`, pin chrome on the subclass, declare children as
ordinary slots, then mount the subclass at a Page (or another Section)
as `toolbar = Toolbar.slot()`.

## kind

section (layout primitive)

## defaults (class-level)

| field     | type                                                                  | default    | notes                                                          |
| --------- | --------------------------------------------------------------------- | ---------- | -------------------------------------------------------------- |
| `gap`     | `int`                                                                 | `4`        | tailwind gap step (`gap-4`); space between children            |
| `align`   | `Literal["start", "center", "end", "stretch", "baseline"]`            | `"center"` | cross-axis (vertical) alignment of children                    |
| `justify` | `Literal["start", "center", "end", "between", "around", "evenly"]`    | `"start"`  | main-axis (horizontal) distribution of children                |
| `wrap`    | `bool`                                                                | `False`    | children wrap to next line on overflow                         |
| `padding` | `int`                                                                 | `0`        | tailwind padding step (`p-{n}`); inner padding around children |

Children are declared as slot fields on the Section body. They become
nested wire-path segments under the section's path.

Example:

```python
class Toolbar(nudle.Row):
    gap = 2
    justify = "between"

    greeting = nudle.HeadingRef.slot()
    submit   = nudle.ButtonRef.slot()


class HomePage(nudle.Page):
    toolbar = Toolbar.slot()


# server-side handles
Toolbar.greeting.store("hello")     # writes HomePage.toolbar.greeting
HomePage.toolbar.submit.clicked()   # listens on HomePage.toolbar.submit
```

A given Section subclass is mounted at exactly one Slot per Index.
Reuse raises at Page-class creation time.

## interactions

| op      | dir           | payload                                                                          | nu method                                                                            | notes                                                  |
| ------- | ------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| `write` | server -> tab | `{"gap"?: int, "align"?: str, "justify"?: str, "wrap"?: bool, "padding"?: int}`  | (no `store_*` on the Section itself in v0.1.0)                                       | partial chrome update from the server. Not used yet.   |

The set of child slots is fixed at mount. Runtime add / remove is not in
v0.1.0; the server re-mounts to change the tree.

## wire payloads

```
// mount field entry, recursive
{
  "path": "HomePage.toolbar",
  "type": "Row",
  "props": {"gap": 2, "align": "center", "justify": "between", "wrap": false, "padding": 0},
  "fields": [
    {"path": "HomePage.toolbar.greeting", "type": "HeadingRef", "props": {...}},
    {"path": "HomePage.toolbar.submit",   "type": "ButtonRef",  "props": {...}}
  ]
}
```

Payload is a msgpack map. Missing keys mean "keep current slice value".

## renderer

`web/src/refs/row.tsx`. A `<div>` with tailwind utility classes:
`flex flex-row`, plus `gap-{gap}`, `items-{align}`, `justify-{justify}`,
`flex-wrap` (when `wrap`), `p-{padding}`. Children are looked up by path
from the store; each is rendered with its registered component inside an
`ErrorBoundary`. Unknown child paths render an inline diagnostic
(`no ref at <path>`).

The mount walker registers a slice for the Row entry AND recurses into
its `fields`, so every leaf has a slice. The Row slice carries an array
of child paths (`children`) for the renderer to iterate.

## slice shape

```
{
  type: "Row",
  value: null,
  gap: number,
  align: string,
  justify: string,
  wrap: boolean,
  padding: number,
  children: string[],
  write: (v: {gap?, align?, justify?, wrap?, padding?}) => void,
}
```

Seeded from `field.props` and the nested `fields` list on mount.

## edge cases

- empty section body: row renders an empty `<div>` with the right classes.
- duplicate child slot name: not possible at the Python level (slot names
  are unique within a Shape).
- nested sections (Row inside a Container, Row inside a Column): supported.
- unknown `align` / `justify` value: stored raw, renderer falls back to default.
- unknown `gap` / `padding` integer (outside the local tailwind step map):
  falls back to the default class for that field.

## non-goals

- no `read`, no `notify`. Server-owned.
- no per-child overrides (per-child padding, ordering, gap).
- no responsive breakpoints.
- no runtime add / remove of children. Re-mount instead.
- no instance multiplexing: one Section subclass = one mount point.
