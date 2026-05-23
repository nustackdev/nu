# ProgressRef

Progress bar showing a fraction in [0, 1] with an optional caption. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field           | type    | default | notes                                                       |
| --------------- | ------- | ------- | ----------------------------------------------------------- |
| `value`         | `float` | `0.0`   | progress in [0, 1]; clamped on the browser side             |
| `caption`       | `str`   | `""`    | optional text shown under the bar; empty hides it           |
| `indeterminate` | `bool`  | `False` | when true the bar animates and `value` is ignored visually  |

Declared as plain class attributes on the python `ProgressRef`. They ship on `mount` under the field entry's `props` key and seed the browser slice without an explicit `write`.

## interactions

| op      | dir           | payload                                                          | nu method                                                            | notes                                                               |
| ------- | ------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `write` | server -> tab | `{"value"?: float, "caption"?: str, "indeterminate"?: bool}`     | `store_value`, `store_caption`, `store_indeterminate`, `store`       | partial update; keys absent from the payload leave the slice as is. |

Four nu methods compile to the same wire op with different payload subsets:

- `store_value(v)` -> `write {"value": v}`
- `store_caption(t)` -> `write {"caption": t}`
- `store_indeterminate(flag)` -> `write {"indeterminate": flag}`
- `store(value, caption=..., indeterminate=...)` -> `write {"value": value, ...}` (omitted kwargs left out)

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.progress", "type": "ProgressRef",
 "props": {"value": 0.0, "caption": "", "indeterminate": false}}

// value only
{"op": "write", "ref": "HomePage.progress", "payload": {"value": 0.42}}

// value plus caption
{"op": "write", "ref": "HomePage.progress", "payload": {"value": 0.42, "caption": "uploading"}}

// flip to indeterminate
{"op": "write", "ref": "HomePage.progress", "payload": {"indeterminate": true}}

// clear the caption (Nu EMPTY -> msgpack nil -> "")
{"op": "write", "ref": "HomePage.progress", "payload": {"caption": null}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value". Nu sentinels on any field encode as msgpack nil; on the browser, nil decodes to `0` for `value`, `""` for `caption`, `false` for `indeterminate`.

## renderer

`web/src/refs/progress.tsx`. A two-row div: the bar (a fixed-height rail with a coloured fill) and an optional caption under it. When `indeterminate` is true, the fill is a partial-width sliding strip animated via tailwind's `animate-pulse`; otherwise the fill width is `value * 100%`. No external shadcn dep.

## slice shape

```
{
  type: "ProgressRef",
  value: number,           // clamped to [0, 1]
  caption: string,
  indeterminate: boolean,
  write: (v: {value?, caption?, indeterminate?}) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice and clamps `value`.

## edge cases

- empty payload (`{}`): no-op, slice unchanged.
- `value` is msgpack nil: stored as `0`.
- `value` out of [0, 1]: clamped on write; negatives go to 0, values above 1 go to 1.
- `value` non-numeric or NaN: coerced via `Number(...)`; NaN goes to 0.
- `caption` is msgpack nil: stored as `""`.
- `indeterminate` is msgpack nil: stored as `false`.
- `indeterminate: true` with a non-zero `value`: both stored; renderer ignores `value` while indeterminate is true.
- slot never written and no `props` on mount: selectors fall back to `0` / `""` / `false`.

## non-goals

- no `append`, no `read`, no `notify`. Single bar, server-owned.
- no buffered / two-tone fills.
- no inline percentage text inside the bar; caption is the only text slot.
- no colour variants (success / warn / danger). One colour for v0.
- no min/max other than [0, 1]; callers normalize.
