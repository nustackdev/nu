---
title: StatRef
---

Big number with a label, optional delta and trend arrow. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field   | type  | default   | notes                                                                  |
| ------- | ----- | --------- | ---------------------------------------------------------------------- |
| `label` | `str` | `""`      | caption shown above the value                                          |
| `value` | `str` | `""`      | the main number, pre-formatted server-side (e.g. `"1,234"`, `"$42k"`)  |
| `delta` | `str` | `""`      | secondary change string (e.g. `"+12%"`, `"-3"`); empty hides the row   |
| `trend` | `str` | `"flat"`  | one of `"up"`, `"down"`, `"flat"`; drives arrow icon + colour          |

Declared as plain class attributes on the python `StatRef`. Shipped once on `mount` under the field entry's `props` key and used to seed the browser slice. Later server -> tab `write` frames override slice values. The server pre-formats numbers to strings; the renderer never parses or computes.

## interactions

| op      | dir           | payload                                                              | nu method                                                  | notes                                                                  |
| ------- | ------------- | -------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------- |
| `write` | server -> tab | `{"label"?: str, "value"?: str, "delta"?: str, "trend"?: str}`       | `store_label`, `store_value`, `store_delta`, `store_trend` | partial update; keys absent from the payload leave the slice as is.    |

Four nu methods compile to the same wire op with different payload subsets:

- `store_label(text)` -> `write {"label": text}`
- `store_value(text)` -> `write {"value": text}`
- `store_delta(text)` -> `write {"delta": text}`
- `store_trend(name)` -> `write {"trend": name}`

No combined `set(...)` in v1. Atomic multi-field updates can issue multiple frames in order; adding `set(...)` later is non-breaking (same wire op).

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "HomePage.revenue", "type": "StatRef", "props": {"label": "", "value": "", "delta": "", "trend": "flat"}}

// label-only update
{"op": "write", "ref": "HomePage.revenue", "payload": {"label": "Revenue"}}

// value-only update
{"op": "write", "ref": "HomePage.revenue", "payload": {"value": "$42,108"}}

// delta-only update
{"op": "write", "ref": "HomePage.revenue", "payload": {"delta": "+12.4%"}}

// trend-only update
{"op": "write", "ref": "HomePage.revenue", "payload": {"trend": "up"}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value". Nu sentinels encode as msgpack nil; on the browser, nil decodes to `""` for the three string fields and `"flat"` for `trend`.

## renderer

`web/src/refs/stat.tsx`. Plain tailwind, no shadcn dep. Local consts `TREND_CLASSES` (`up -> text-green-600`, `down -> text-red-600`, `flat -> text-gray-500`) and `TREND_ARROW` (`up -> "↑"`, `down -> "↓"`, `flat -> "→"`) drive the delta row. Label row hides when `label == ""`; delta row hides when `delta == ""`.

## slice shape

```
{
  type: "StatRef",
  value: string,
  label: string,
  delta: string,
  trend: string,
  write: (v: {label?, value?, delta?, trend?}) => void,
}
```

The protocol-level `value: null` marker is dropped; the domain `value` field takes its slot directly (same precedent as `BadgeRef`). Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice.

## edge cases

- empty payload (`{}`): no-op, slice unchanged.
- string field arrives as msgpack nil: stored as `""` (`label` / `value` / `delta`) or `"flat"` (`trend`).
- `trend` string outside the three known names: stored raw; renderer falls back to the `flat` class + arrow. No error frame.
- `delta == ""`: the delta row is hidden entirely (arrow + text both hidden).
- `label == ""`: the label row is hidden; the value still renders.
- `value == ""`: renders an empty big slot; the renderer does not substitute a dash. The server ships `"-"` or `"--"` when it wants a placeholder.
- no max length on any field; truncation is a css concern.
- no client-side number parsing or locale formatting.

## non-goals

- no `append`, no `read`, no `notify`. Server-owned, single op.
- no click / hover / drilldown. A clickable stat belongs to a separate Ref.
- no inline sparkline. Compose `StatRef` next to `SparklineRef` via a `Row`.
- no auto-derivation of `trend` from `delta`'s sign. Server decides.
- no icon slot beyond the trend arrow; no per-instance colour overrides.
- no number / currency formatting on the browser. Server formats.
- no combined `set(...)` method in v1.
