---
title: Sparkline
---

Small inline trend line. Display-only, server-owned. No axes, tooltip, grid, or legend. recharts on the browser.

## kind

display

## defaults (class-level)

| field        | type   | default     | notes                                            |
| ------------ | ------ | ----------- | ------------------------------------------------ |
| `color`      | `str`  | `"#2563eb"` | line stroke colour (any css colour string)       |
| `height`     | `int`  | `32`        | fixed pixel height of the line area; min 8       |
| `max_points` | `int`  | `100`       | ring-buffer cap; oldest points drop on overflow  |

Declared as plain class attributes on the python `Sparkline`. They ship on `mount` under the field entry's `props` key and seed the browser slice without an explicit `write`.

## interactions

| op       | dir           | payload                                                              | nu method                                                                       | notes                                                          |
| -------- | ------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `write`  | server -> tab | `{"points"?: [[x, y], ...], "color"?: str, "height"?: int, "max_points"?: int}` | `store`, `store_points`, `store_color`, `store_height`, `store_max_points`, `clear` | partial update; absent keys leave the slice as is.             |
| `append` | server -> tab | `[x, y]`                                                             | `append`                                                                        | pushes one point; tab drops oldest once length exceeds `max_points`. |

Nu methods compile to the same wire ops with different payload subsets:

- `store_points(seq)` -> `write {"points": seq}`
- `store_color(c)` -> `write {"color": c}`
- `store_height(n)` -> `write {"height": n}`
- `store_max_points(n)` -> `write {"max_points": n}`
- `store(points, color=..., height=..., max_points=...)` -> `write` of the present keys
- `clear()` -> `write {"points": []}` (convenience; not a new op)
- `append(x, y)` -> `append [x, y]`

Legacy: `store({"points": [...]})` (first positional arg a dict) still works; the dict is unwrapped to `{"points": ...}`. Flat `[y0, y1, ...]` on `points` is accepted and auto-x'd to `0..n-1`.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "Dashboard.pulse", "type": "Sparkline",
 "props": {"color": "#2563eb", "height": 32, "max_points": 100}}

// replace series
{"op": "write", "ref": "Dashboard.pulse",
 "payload": {"points": [[0, 1], [1, 4], [2, 9]]}}

// recolor / resize
{"op": "write", "ref": "Dashboard.pulse",
 "payload": {"color": "#16a34a", "height": 48}}

// shrink the ring buffer
{"op": "write", "ref": "Dashboard.pulse", "payload": {"max_points": 20}}

// clear
{"op": "write", "ref": "Dashboard.pulse", "payload": {"points": []}}

// one new point
{"op": "append", "ref": "Dashboard.pulse", "payload": [42, 0.91]}
```

Payload is a msgpack map (for `write`) or a 2-array (for `append`). Nu sentinels on `y` encode as msgpack nil; on the browser nil becomes a gap in the line (`connectNulls={false}`).

## renderer

`web/src/refs/sparkline.tsx`. recharts `LineChart` inside a `ResponsiveContainer` at `style={{ height }} w-full`. No `XAxis`, no `YAxis`, no `CartesianGrid`, no `Tooltip`, no legend. Domain is implicit from data. Line stroke uses `color` at `strokeWidth={1.5}` with `dot={false}` and `connectNulls={false}`.

## slice shape

```
{
  type: "Sparkline",
  value: { points: [[x, y|null], ...] },
  color: string,
  height: number,
  max_points: number,
  write: (v: partial) => void,
  append: (v: [x, y]) => void,
}
```

Seeded from `field.props` on mount. `write` merges the partial payload and, when `max_points` shrinks, re-trims the existing buffer. `append` pushes one point and drops the oldest once length exceeds `max_points`. Tab holds no local-only state.

## edge cases

- empty / never-written `points`: render the empty container (no line). no throw.
- empty `write` payload (`{}`): no-op, slice unchanged.
- `points` with non-numeric x: x falls back to the point's index.
- `points` with non-numeric, `NaN`, or `Infinity` y: y stored as `null`, drawn as a gap.
- `height <= 0` or non-numeric on `write`: falls back to default (`32`). values below 8 clamp to 8.
- `max_points <= 0` or non-numeric: clamps to `1`. non-finite falls back to default.
- `max_points` shrinks below current buffer length: tail-trim immediately.
- `color` non-string or nil: keeps current value.
- `append` with malformed payload (not a 2-element array): frame ignored.
- `append` when slice missing: no-op.
- second `mount`: slice is rebuilt from `props`; prior buffer is dropped.
- flat Y array on `write.points`: auto-x = 0..n-1 (legacy).

## non-goals

- no axes, no axis labels, no tooltip, no grid, no legend.
- no x-format switch (`time` vs `number`). x is opaque positional.
- no area fill, no markers, no multi-series.
- no click / hover interactions.
- no tab-owned state. no `read`, no `notify`.
- no responsive height; height is a fixed integer.
