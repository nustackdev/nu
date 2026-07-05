---
title: DividerRef
---

Horizontal rule with optional inline label. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field   | type                                 | default    | notes                                                                             |
| ------- | ------------------------------------ | ---------- | --------------------------------------------------------------------------------- |
| `label` | `str`                                | `""`       | empty -> plain `<hr>`; non-empty -> inline label with a rule on each side         |
| `align` | `Literal["left", "center", "right"]` | `"center"` | inline label position; no visible effect when `label` is `""`                     |

Declared as plain class attributes on the python `DividerRef`. Both fields ship on `mount` under the field entry's `props` key and seed the browser slice (no explicit `write` needed). Later server -> tab writes override slice values.

## interactions

| op      | dir           | payload                          | nu method                             | notes                                                              |
| ------- | ------------- | -------------------------------- | ------------------------------------- | ------------------------------------------------------------------ |
| `write` | server -> tab | `{"label"?: str, "align"?: str}` | `store_label`, `store_align`, `store` | partial update; keys absent from the payload leave the slice as is |

Three nu methods compile to the same wire op with different payload subsets:

- `store_label(text)` -> `write {"label": text}`
- `store_align(side)` -> `write {"align": side}`
- `store(label, align=...)` -> `write {"label": label, ...}` with `align` included only when passed.

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "HomePage.divider", "type": "DividerRef", "props": {"label": "", "align": "center"}}

// label-only update
{"op": "write", "ref": "HomePage.divider", "payload": {"label": "or"}}

// align-only update
{"op": "write", "ref": "HomePage.divider", "payload": {"align": "left"}}

// combined update
{"op": "write", "ref": "HomePage.divider", "payload": {"label": "section two", "align": "center"}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value". Nu sentinels encode as msgpack nil; on the browser, nil decodes to `""` for `label` and `"center"` for `align`.

## renderer

`web/src/refs/divider.tsx`. Tailwind-only, no shadcn dep. When `label` is `""`, renders `<hr className="my-4 border-t border-border" />`. When `label` is non-empty, renders a flex row with two `<span>` rule segments and the label between them. The flex ratios encode `align`:

- `"center"` -> both segments `flex-1`
- `"left"`   -> left `w-4 flex-none`, right `flex-1`
- `"right"`  -> left `flex-1`, right `w-4 flex-none`

Align outside the three known values falls back to `"center"`.

## slice shape

```
{
  type: "DividerRef",
  value: null,
  label: string,
  align: string,
  write: (v: {label?: unknown, align?: unknown}) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice.

## edge cases

- empty payload (`{}`): no-op, slice unchanged.
- non-object payload (string, number, nil): ignored, slice unchanged.
- `label` is msgpack nil: stored as `""` (renders as plain `<hr>`).
- `align` is nil or outside the three known names: stored as `"center"`.
- slot never written and no `props` on mount: selector defaults kick in (`""` / `"center"`).
- whitespace-only `label`: treated as non-empty (renderer does not trim); the server is responsible for sending `""` to get a plain rule.

## non-goals

- no vertical / orientation toggle. A vertical divider is a separate Ref if ever needed.
- no thickness / color / dashed-style props. Tailwind border defaults only.
- no `append`, no `read`, no `notify`. Server-owned display Ref.
- no icon slot beside the label.
- no click / hover.
