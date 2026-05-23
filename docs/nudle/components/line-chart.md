# LineChart

Time-series line chart. Display-only, server-owned. recharts on the browser. Supports a single line (legacy `points` payload) or multiple named series (multi-series `series` payload).

## kind

display

## defaults (class-level)

| field          | type                          | default     | notes                                                                       |
| -------------- | ----------------------------- | ----------- | --------------------------------------------------------------------------- |
| `x_label`      | `str`                         | `""`        | X axis label; empty hides it                                                |
| `y_label`      | `str`                         | `""`        | Y axis label; empty hides it                                                |
| `color`        | `str`                         | `"#2563eb"` | line stroke colour for single-series mode (any css colour string)           |
| `max_points`   | `int`                         | `500`       | sliding window cap; oldest points drop when buffer goes over                |
| `x_format`     | `Literal["number", "time"]`   | `"number"`  | x-axis formatter; `"time"` reads x as ms since epoch                        |
| `show_legend`  | `bool`                        | `False`     | when true and multi-series, render a recharts legend                        |
| `show_tooltip` | `bool`                        | `True`      | when false, no tooltip; default matches recharts default                    |
| `palette`      | `list[str]`                   | `[]`        | hex / css colours cycled across multi-series; empty -> recharts default     |

Declared as plain class attributes on the python `LineChart`. They ship on `mount` under the field entry's `props` key and seed the browser slice without an explicit `write`.

## interactions

| op       | dir           | payload                                                                                                                                                                                                                | nu method                                                                                                                                                                                                                                  | notes                                                                                          |
| -------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `write`  | server -> tab | partial map with any of: `points`, `series`, `x_label`, `y_label`, `color`, `max_points`, `x_format`, `show_legend`, `show_tooltip`, `palette`                                                                       | `store`, `store_points`, `store_series`, `store_x_label`, `store_y_label`, `store_color`, `store_max_points`, `store_x_format`, `store_show_legend`, `store_show_tooltip`, `store_palette`, `clear`                                        | partial update; absent keys leave the slice as is. `points` puts the slice in single-series mode; `series` puts it in multi-series mode. |
| `append` | server -> tab | single-series: `[x, y]`; multi-series: `{"name": str, "x": x, "y": y}`                                                                                                                                                | `append`, `append_series`                                                                                                                                                                                                                  | pushes one point; tab drops oldest once a series length exceeds `max_points`.                  |

Nu methods compile to the same wire ops with different payload subsets:

- `store_points(seq)` -> `write {"points": seq}` (single-series)
- `store_series(list)` -> `write {"series": list}` (multi-series)
- `store_x_label(t)` / `store_y_label(t)` -> `write {"x_label" | "y_label": t}`
- `store_color(c)` -> `write {"color": c}`
- `store_max_points(n)` -> `write {"max_points": n}`
- `store_x_format(name)` -> `write {"x_format": name}`
- `store_show_legend(flag)` -> `write {"show_legend": flag}`
- `store_show_tooltip(flag)` -> `write {"show_tooltip": flag}`
- `store_palette(colors)` -> `write {"palette": colors}`
- `store(points=..., series=..., x_label=..., y_label=..., color=..., max_points=..., x_format=..., show_legend=..., show_tooltip=..., palette=...)` -> `write` of the present keys
- `clear()` -> `write {"points": []}` (convenience; not a new op)
- `append(x, y)` -> `append [x, y]` (single-series)
- `append_series(name, x, y)` -> `append {"name": name, "x": x, "y": y}` (multi-series)

Legacy: `store({"points": [...]})` (first positional arg a dict) still works; the dict is unwrapped to `{"points": ...}`. Flat `[y0, y1, ...]` on `points` is accepted and auto-x'd to `0..n-1`. Single-series payload (`points`) stays valid -- the chart is backwards compatible.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "Dashboard.history", "type": "LineChart",
 "props": {"x_label": "", "y_label": "", "color": "#2563eb",
           "max_points": 500, "x_format": "number",
           "show_legend": false, "show_tooltip": true, "palette": []}}

// single-series: replace points (legacy, still valid)
{"op": "write", "ref": "Dashboard.history",
 "payload": {"points": [[0, 1], [1, 4], [2, 9]]}}

// multi-series: replace the whole series list
{"op": "write", "ref": "Dashboard.history",
 "payload": {"series": [
   {"name": "cpu", "points": [[0, 0.1], [1, 0.3]], "color": "#2563eb"},
   {"name": "gpu", "points": [[0, 0.4], [1, 0.5]]}
 ]}}

// labels + colour
{"op": "write", "ref": "Dashboard.history",
 "payload": {"x_label": "tick", "y_label": "wishes", "color": "#16a34a"}}

// toggle legend / tooltip / palette
{"op": "write", "ref": "Dashboard.history",
 "payload": {"show_legend": true, "show_tooltip": false,
             "palette": ["#2563eb", "#16a34a", "#f59e0b"]}}

// switch to time mode
{"op": "write", "ref": "Dashboard.history", "payload": {"x_format": "time"}}

// clear
{"op": "write", "ref": "Dashboard.history", "payload": {"points": []}}

// one new point (single-series)
{"op": "append", "ref": "Dashboard.history", "payload": [42, 0.91]}

// one new point on a named series (multi-series)
{"op": "append", "ref": "Dashboard.history",
 "payload": {"name": "cpu", "x": 42, "y": 0.91}}
```

Payload is a msgpack map (for `write`) or a 2-array / map (for `append`). Nu sentinels on `y` encode as msgpack nil; on the browser nil becomes a gap in the line (`connectNulls={false}`).

## renderer

`web/src/refs/line-chart.tsx`. recharts `LineChart` inside a `ResponsiveContainer` at `h-64 w-full`. The renderer auto-detects mode from the slice value: `value.series` present -> multi-series, otherwise single-series from `value.points`. X axis is numeric with `domain={["dataMin", "dataMax"]}`. When `x_format === "time"`, x ticks (and tooltip labels) render as `HH:MM:SS` from ms since epoch. When `x_label` / `y_label` are non-empty the axes show them via the recharts `label` prop. Single-series stroke uses `color`; multi-series stroke uses each series' `color` if present, otherwise the next entry from `palette` (cycled), otherwise the recharts default. A light `CartesianGrid` is drawn for readability. `show_tooltip` toggles the `Tooltip`; `show_legend` toggles the `Legend` in multi-series mode only. No external shadcn dep.

## slice shape

```
{
  type: "LineChart",
  value: { points?: [[x, y|null], ...], series?: [{name, points, color?}, ...] },
  x_label: string,
  y_label: string,
  color: string,
  max_points: number,
  x_format: "number" | "time",
  show_legend: boolean,
  show_tooltip: boolean,
  palette: string[],
  write: (v: partial) => void,
  append: (v: [x, y] | {name, x, y}) => void,
}
```

Seeded from `field.props` on mount. `write` merges the partial payload; if `points` arrives the slice flips to single-series, if `series` arrives it flips to multi-series. When `max_points` shrinks, the existing buffer re-trims. `append` of a 2-array pushes onto the single-series buffer; `append` of a `{name, x, y}` map pushes onto (or creates) the named series in multi-series mode. Each series buffer trims independently to `max_points`.

## edge cases

- empty `write` payload (`{}`): no-op, slice unchanged.
- `points` with non-numeric x: x falls back to the point's index.
- `points` with non-numeric or NaN y: y stored as `null`, drawn as a gap.
- `max_points <= 0` or non-numeric: clamped to `1`.
- `max_points` shrinks below current buffer length: tail-trim immediately (both modes).
- `x_format` unknown string or nil: falls back to `"number"`.
- `color` non-string or nil: keeps current value.
- `append` when slice missing: no-op.
- `append` with a non-2-array, non-`{name,x,y}` payload: no-op for the push.
- `append_series` with unknown `name`: creates a new series with that name.
- multi-series `append` while slice is in single-series mode (or vice versa): the slice flips mode; previous-mode buffer is dropped.
- flat Y array on `write.points`: auto-x = 0..n-1 (legacy).
- `series` entry with no `color`: renderer picks from `palette` (cycled), else recharts default.
- `palette` non-list or with non-string entries: filtered down to strings; empty palette falls back to recharts default colour.
- `show_legend` true but single-series mode: legend is not rendered.

## non-goals

- no zoom or brush.
- no client-side downsampling beyond the sliding window cap.
- no read / notify ops. server pushes only.
- no per-series dot / stroke-width / dash customisation beyond `color`.
