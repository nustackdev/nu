---
title: Column
---

Vertical layout primitive. A `Column` is a Shape (Section), not a Ref. It
stacks its child slots vertically with optional gap, alignment,
justification, and padding. Display-only, server-owned.

Subclass `nudle.Column`, pin chrome on the subclass, declare children as
ordinary slots, then mount the subclass at a Page (or another Section).

## kind

section (layout primitive)

## defaults (class-level)

| field     | type                                                       | default     | notes                                       |
| --------- | ---------------------------------------------------------- | ----------- | ------------------------------------------- |
| `gap`     | `int` (tailwind unit)                                      | `4`         | maps to `gap-<n>`                           |
| `align`   | `Literal["start", "center", "end", "stretch"]`             | `"stretch"` | cross-axis (horizontal) alignment           |
| `justify` | `Literal["start", "center", "end", "between", "around"]`   | `"start"`   | main-axis (vertical) distribution           |
| `padding` | `int` (tailwind unit)                                      | `0`         | inner padding; maps to `p-<n>`              |

## children

Children are declared as ordinary slots on the Section body:

```python
class Toolbar(nudle.Column):
    gap = 2
    padding = 4

    title  = nudle.HeadingRef.slot()
    status = nudle.BadgeRef.slot()


class HomePage(nudle.Page):
    toolbar = Toolbar.slot()


# server-side handles
Toolbar.title.store("home")     # writes HomePage.toolbar.title
Toolbar.status.store_label("ok")
```

`Page.mount_fields` recurses into Section slots, emitting a nested
`fields` list under the section's entry. Wire paths are
`HomePage.toolbar.title`, `HomePage.toolbar.status`.

## interactions

| op      | dir           | payload                                              |
| ------- | ------------- | ---------------------------------------------------- |
| `write` | server -> tab | `{"gap"?, "align"?, "justify"?, "padding"?}`         |

Partial update: keys absent leave the slice as is.

## wire payloads

```
// mount field entry, recursive
{
  "path": "HomePage.toolbar",
  "type": "Column",
  "props": {"gap": 2, "align": "stretch", "justify": "start", "padding": 4},
  "fields": [
    {"path": "HomePage.toolbar.title",  "type": "HeadingRef", "props": {...}},
    {"path": "HomePage.toolbar.status", "type": "BadgeRef",   "props": {...}}
  ]
}

// runtime visual update
{"op": "write", "ref": "HomePage.toolbar", "payload": {"gap": 6}}
```

## renderer

`web/src/refs/column.tsx`. A `<div>` with tailwind `flex flex-col` plus
class names per slice field. The renderer reads `children` (an array of
child wire paths) from the slice and emits one component per child,
dispatched via the global renderers map.

The mount walker registers a slice for the Column entry AND recurses into
its `fields`, so every leaf has a slice.

## slice shape

```
{
  type: "Column",
  value: null,
  gap: number,
  align: string,
  justify: string,
  padding: number,
  children: string[],
  write: (v: {gap?, align?, justify?, padding?}) => void,
}
```

## edge cases

- empty section body: renders an empty `<div>` (visible only if padding > 0).
- unknown align / justify: stored raw; renderer falls back to defaults.
- gap / padding non-integer: coerced via `Number(...)`; NaN -> defaults.
- child slice missing from the registry: renderer skips it; sibling rendering continues.
- nested sections: any Section may declare another Section slot as a child.

## non-goals

- no scroll (`overflow` defaults to visible).
- no per-child overrides from the parent (no `margin-self`, no per-child `align`).
- no responsive breakpoints.
- no `read`, no `notify`. Column is server-owned.
- no instance multiplexing: one Section subclass = one mount point.
