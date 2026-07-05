---
title: HeadingRef
---

In-body heading with selectable level and text alignment. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field   | type                                  | default  | notes                                                |
| ------- | ------------------------------------- | -------- | ---------------------------------------------------- |
| `label` | `str`                                 | `""`     | heading text                                         |
| `level` | `int` in `{1, 2, 3, 4}`               | `1`      | maps to `<h1>` .. `<h4>` on the browser side         |
| `align` | `Literal["left", "center", "right"]`  | `"left"` | text alignment, applied as a tailwind utility class  |

Declared as plain class attributes on the python `HeadingRef`. All three are shipped on `mount` under the field entry's `props` key and used to seed the browser slice (no explicit `write` needed). Later server -> tab writes override slice values.

## interactions

| op      | dir           | payload                                              | nu method                                              | notes                                                                |
| ------- | ------------- | ---------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------- |
| `write` | server -> tab | `{"label"?: str, "level"?: int, "align"?: str}`      | `store_label`, `store_level`, `store_align`, `store`   | partial update; keys absent from the payload leave the slice as is.  |

Four nu methods compile to the same wire op with different payload subsets:

- `store_label(text)` -> `write {"label": text}`
- `store_level(n)` -> `write {"level": n}`
- `store_align(side)` -> `write {"align": side}`
- `store(label, level=..., align=...)` -> `write {"label": label, ...}` with optional keys included only when passed.

A bare string payload (`write "some heading"`) is accepted as a legacy shorthand equivalent to `{"label": "some heading"}`. New callers should use the dict form.

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "HomePage.heading", "type": "HeadingRef", "props": {"label": "", "level": 1, "align": "left"}}

// label-only update
{"op": "write", "ref": "HomePage.heading", "payload": {"label": "welcome"}}

// level-only update
{"op": "write", "ref": "HomePage.heading", "payload": {"level": 2}}

// combined update
{"op": "write", "ref": "HomePage.heading", "payload": {"label": "section", "level": 2, "align": "center"}}

// legacy shorthand
{"op": "write", "ref": "HomePage.heading", "payload": "welcome"}
```

Payload is a msgpack map (or a bare string for the legacy form). Missing keys mean "keep current slice value". Nu sentinels on any field encode as msgpack nil; on the browser, nil decodes to `""` for `label`, `1` for `level`, and `"left"` for `align`.

## renderer

`web/src/refs/heading.tsx`. Renders `<h1>` .. `<h4>` chosen by `level`, with tailwind utility classes per level (`text-3xl/2xl/xl/lg` plus font weight and bottom margin) and per align (`text-left/center/right`). Level outside `{1..4}` clamps to `1`; align outside the three known values falls back to `"left"`. No external shadcn dep; class maps are local consts (`LEVEL_CLASSES`, `ALIGN_CLASSES`).

## slice shape

```
{
  type: "HeadingRef",
  value: null,
  label: string,
  level: number,
  align: string,
  write: (v: string | {label?, level?, align?}) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice; a bare string payload is treated as `{label: <string>}`.

## edge cases

- empty payload (`{}`): no-op, slice unchanged.
- `label` is msgpack nil: stored as `""`.
- `level` is nil or non-integer: stored as `1`.
- `level` outside `{1..4}`: clamped into range (`0` -> `1`, `7` -> `4`).
- `align` is nil or outside the three known names: stored as `"left"`.
- bare string payload: assigned to `label`; other slice fields untouched.
- slot never written and no `props` on mount: selector defaults kick in (`""` / `1` / `"left"`).

## non-goals

- no `append`, no `read`, no `notify`. Single heading, server-owned.
- no h5 / h6 levels (rare in practice; can be added later without breaking wire shape).
- no anchor / id slot for in-page links.
- no icon / decoration prefix.
- no click / hover. A clickable heading is a `LinkRef` or `ButtonRef` job.
- no `caps` flags on mount; deferred catalog-wide.
