---
title: GaugeRef
---

Circular dial showing a ratio in [0, 1] with an optional caption and a color variant. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field     | type    | default     | notes                                                                 |
| --------- | ------- | ----------- | --------------------------------------------------------------------- |
| `value`   | `float` | `0.0`       | ratio in [0, 1]; clamped on the browser side                          |
| `caption` | `str`   | `""`        | optional text shown under the dial; empty hides it                    |
| `variant` | `str`   | `"neutral"` | one of `"neutral"` / `"ok"` / `"warn"` / `"danger"`; picks arc color  |

Declared as plain class attributes on the python `GaugeRef`. They ship on `mount` under the field entry's `props` key and seed the browser slice without an explicit `write`. Variant is a fixed enum, not a threshold rule; the server decides which variant to show via `store_variant`. The browser does no automatic banding.

## interactions

| op      | dir           | payload                                                                    | nu method                                                                | notes                                                               |
| ------- | ------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| `write` | server -> tab | `{"value"?: float, "caption"?: str, "variant"?: str}`                      | `store_value`, `store_caption`, `store_variant`, `store`                 | partial update; keys absent from the payload leave the slice as is. |

Four nu methods compile to the same wire op with different payload subsets:

- `store_value(v)` -> `write {"value": v}`
- `store_caption(t)` -> `write {"caption": t}`
- `store_variant(name)` -> `write {"variant": name}`
- `set(value, caption=..., variant=...)` -> `write {"value": value, ...}` (omitted kwargs left out)

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "HomePage.cpu", "type": "GaugeRef",
 "props": {"value": 0.0, "caption": "", "variant": "neutral"}}

// value only
{"op": "write", "ref": "HomePage.cpu", "payload": {"value": 0.42}}

// value plus caption plus variant
{"op": "write", "ref": "HomePage.cpu", "payload": {"value": 0.93, "caption": "cpu", "variant": "danger"}}

// caption only
{"op": "write", "ref": "HomePage.cpu", "payload": {"caption": "load average"}}

// reset everything (Nu sentinels -> msgpack nil)
{"op": "write", "ref": "HomePage.cpu", "payload": {"value": null, "caption": null, "variant": null}}
```

Payload is a msgpack map. Missing keys mean "keep current slice value". Nu sentinels on any field encode as msgpack nil; on the browser, nil decodes to `0` for `value`, `""` for `caption`, `"neutral"` for `variant`.

## renderer

`web/src/refs/gauge.tsx`. An svg dial with a fixed background track circle and an arc whose length is `value * circumference` drawn over it. The percent (`value * 100` rounded) is centered inside the dial. Variant maps to a stroke color via a small lookup; unknown variants fall back to neutral. Caption sits under the dial when non-empty. No external shadcn dep.

## slice shape

```
{
  type: "GaugeRef",
  value: number,        // clamped to [0, 1]
  caption: string,
  variant: "neutral" | "ok" | "warn" | "danger",
  write: (v: {value?, caption?, variant?}) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into the slice, clamps `value`, and normalizes `variant`.

## edge cases

- empty payload (`{}`): no-op, slice unchanged.
- `value` is msgpack nil: stored as `0`.
- `value` out of [0, 1]: clamped on write; negatives go to 0, values above 1 go to 1.
- `value` non-numeric, NaN, or Infinity: coerced via `Number(...)`; non-finite goes to 0.
- `caption` is msgpack nil: stored as `""`. Plain text only; no markdown, no html.
- `variant` is msgpack nil: stored as `"neutral"`.
- unknown `variant` string: stored as `"neutral"` (no throw, no error frame).
- partial write `{"caption": "..."}` does not reset `value` or `variant`.
- slot never written and no `props` on mount: selectors fall back to `0` / `""` / `"neutral"`.

## non-goals

- no thresholds or auto-banding inside the renderer; variant is set explicitly by the server.
- no animation timing controls. css transitions are fine but no exposed knob.
- no min/max range (always [0, 1]); callers normalize on the Nu side.
- no indeterminate spinner mode (ProgressRef covers that).
- no `notify` / `read`; server-owned only.
- no click / hover interactions.
- no embedded legends, tick marks, or multi-arc displays.
