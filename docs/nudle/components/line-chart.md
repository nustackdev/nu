# LineChart

Time-series line chart. Display-only, server-owned. recharts on the browser.

## kind

display

## defaults (class-level)

| field        | type                          | default     | notes                                                              |
| ------------ | ----------------------------- | ----------- | ------------------------------------------------------------------ |
| `x_label`    | `str`                         | `""`        | X axis label; empty hides it                                       |
| `y_label`    | `str`                         | `""`        | Y axis label; empty hides it                                       |
| `color`      | `str`                         | `"#2563eb"` | line stroke colour (any css colour string)                         |
| `max_points` | `int`                         | `500`       | sliding window cap; oldest points drop when buffer goes over       |
| `x_format`   | `Literal["number", "time"]`   | `"number"`  | x-axis formatter; `"time"` reads x as ms since epoch               |

Declared as plain class attributes on the python `LineChart`. They ship on `mount` under the field entry's `props` key and seed the browser slice without an explicit `write`.

## interactions

| op       | dir           | payload                                                                                                                       | nu method                                                                                                                            | notes                                                                          |
| -------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| `write`  | server -> tab | `{"points"?: [[x, y], ...], "x_label"?: str, "y_label"?: str, "color"?: str, "max_points"?: int, "x_format"?: str}`           | `store`, `store_points`, `store_x_label`, `store_y_label`, `store_color`, `store_max_points`, `store_x_format`, `clear`              | partial update; absent keys leave the slice as is.                             |
| `append` | server -> tab | `[x, y]`                                                                                                                      | `append`                                                                                                                              | pushes one point; tab drops oldest once length exceeds `max_points`.           |

Nu methods compile to the same wire ops with different payload subsets:

- `store_points(seq)` -> `write {"points": seq}`
- `store_x_label(t)` / `store_y_label(t)` -> `write {"x_label" | "y_label": t}`
- `store_color(c)` -> `write {"color": c}`
- `store_max_points(n)` -> `write {"max_points": n}`
- `store_x_format(name)` -> `write {"x_format": name}`
- `store(points, x_label=..., y_label=..., color=..., max_points=..., x_format=...)` -> `write` of the present keys
- `clear()` -> `write {"points": []}` (convenience; not a new op)
- `append(x, y)` -> `append [x, y]`

Legacy: `store({"points": [...]})` (first positional arg a dict) still works; the dict is unwrapped to `{"points": ...}`. Flat `[y0, y1, ...]` on `points` is accepted and auto-x'd to `0..n-1`.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "Dashboard.history", "type": "LineChart",
 "props": {"x_label": "", "y_label": "", "color": "#2563eb",
           "max_points": 500, "x_format": "number"}}

// replace series
{"op": "write", "ref": "Dashboard.history",
 "payload": {"points": [[0, 1], [1, 4], [2, 9]]}}

// labels + colour
{"op": "write", "ref": "Dashboard.history",
 "payload": {"x_label": "tick", "y_label": "wishes", "color": "#16a34a"}}

// switch to time mode
{"op": "write", "ref": "Dashboard.history", "payload": {"x_format": "time"}}

// clear
{"op": "write", "ref": "Dashboard.history", "payload": {"points": []}}

// one new point
{"op": "append", "ref": "Dashboard.history", "payload": [42, 0.91]}
```

Payload is a msgpack map (for `write`) or a 2-array (for `append`). Nu sentinels on `y` encode as msgpack nil; on the browser nil becomes a gap in the line (`connectNulls={false}`).

## renderer

`web/src/refs/line-chart.tsx`. recharts `LineChart` inside a `ResponsiveContainer` at `h-64 w-full`. X axis is numeric with `domain={["dataMin", "dataMax"]}`. When `x_format === "time"`, x ticks (and tooltip labels) render as `HH:MM:SS` from ms since epoch. When `x_label` / `y_label` are non-empty the axes show them. Line stroke uses `color`. A light `CartesianGrid` is drawn for readability. No external shadcn dep.

## slice shape

```
{
  type: "LineChart",
  value: { points: [[x, y|null], ...] },
  x_label: string,
  y_label: string,
  color: string,
  max_points: number,
  x_format: "number" | "time",
  write: (v: partial) => void,
  append: (v: [x, y]) => void,
}
```

Seeded from `field.props` on mount. `write` merges the partial payload and, when `max_points` shrinks, re-trims the existing buffer. `append` pushes one point and drops the oldest once length exceeds `max_points`.

## edge cases

- empty `write` payload (`{}`): no-op, slice unchanged.
- `points` with non-numeric x: x falls back to the point's index.
- `points` with non-numeric or NaN y: y stored as `null`, drawn as a gap.
- `max_points <= 0` or non-numeric: clamped to `1`.
- `max_points` shrinks below current buffer length: tail-trim immediately.
- `x_format` unknown string or nil: falls back to `"number"`.
- `color` non-string or nil: keeps current value.
- `append` when slice missing: no-op.
- `append` with a non-2-array payload: no-op for the push (slice still re-trims).
- flat Y array on `write.points`: auto-x = 0..n-1 (legacy).

## non-goals

- no multi-series. one line per chart.
- no zoom, brush, or legend.
- no client-side downsampling beyond the sliding window cap.
- no read / notify ops. server pushes only.
