---
title: AreaChart
---

Filled line chart. Single series or stacked multi-series with a sliding window. Display-only, server-owned. recharts on the browser.

## kind

display

## defaults (class-level)

| field        | type                          | default          | notes                                                                                       |
| ------------ | ----------------------------- | ---------------- | ------------------------------------------------------------------------------------------- |
| `x_label`    | `str`                         | `""`             | x-axis label; empty hides it                                                                |
| `y_label`    | `str`                         | `""`             | y-axis label; empty hides it                                                                |
| `series`     | `list[str]`                   | `["value"]`      | series names. order is render order (bottom -> top when stacked). length sets the slot count |
| `colors`     | `list[str]`                   | `["#2563eb"]`    | stroke + fill colour per series; cycles if shorter than `series`. fill uses alpha 0.25      |
| `stacked`    | `bool`                        | `False`          | when true the areas stack on y; when false they overlay                                     |
| `max_points` | `int`                         | `500`            | sliding window cap; oldest rows drop when buffer goes over                                  |
| `x_format`   | `Literal["number", "time"]`   | `"number"`       | x-axis formatter; `"time"` reads x as ms since epoch and renders `HH:MM:SS`                 |

Plain class attributes on the python `AreaChart`. Shipped under the field entry's `props` key on `mount` and seed the browser slice with no explicit `write`.

For a single series, the defaults `series = ["value"]` and `colors = ["#2563eb"]` let callers ignore the multi-series machinery entirely.

## interactions

| op       | dir           | payload                                                                                                                                                | nu method                                                                                                                                                | notes                                                                                                                          |
| -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `write`  | server -> tab | `{"points"?: [[x, y0, y1, ...]], "series"?: [str], "colors"?: [str], "stacked"?: bool, "x_label"?: str, "y_label"?: str, "max_points"?: int, "x_format"?: str}` | `store`, `store_points`, `store_series`, `store_colors`, `store_stacked`, `store_x_label`, `store_y_label`, `store_max_points`, `store_x_format`, `clear` | partial update; absent keys leave the slice as is. each row in `points` is one x followed by one y per series, in `series` order |
| `append` | server -> tab | `[x, y0, y1, ...]`                                                                                                                                     | `append`                                                                                                                                                 | pushes one row. row length must be `1 + len(series)`. tab drops oldest once length exceeds `max_points`                       |

Nu methods compile to the same wire ops with different payload subsets:

- `store_points(rows)` -> `write {"points": rows}`
- `store_series(names)` -> `write {"series": names}`
- `store_colors(colors)` -> `write {"colors": colors}`
- `store_stacked(flag)` -> `write {"stacked": flag}`
- `store_x_label(t)` / `store_y_label(t)` -> `write {"x_label" | "y_label": t}`
- `store_max_points(n)` -> `write {"max_points": n}`
- `store_x_format(name)` -> `write {"x_format": name}`
- `store(points=..., series=..., colors=..., stacked=..., x_label=..., y_label=..., max_points=..., x_format=...)` -> `write` of the present keys
- `clear()` -> `write {"points": []}`
- `append(x, *ys)` -> `append [x, *ys]`

Stacked vs overlay is a render-time toggle, not a payload shape change. The wire shape is the same in both modes: one row carries all series' y-values for that x.

## wire payloads

Stacked multi-series with `series = ["cpu", "mem", "io"]`, `colors = ["#2563eb", "#16a34a", "#dc2626"]`:

```
// mount field entry
{"path": "Dashboard.load", "type": "AreaChart",
 "props": {"x_label": "", "y_label": "",
           "series": ["cpu", "mem", "io"],
           "colors": ["#2563eb", "#16a34a", "#dc2626"],
           "stacked": true,
           "max_points": 500, "x_format": "number"}}

// replace series buffer (one row per x; rows are [x, y_cpu, y_mem, y_io])
{"op": "write", "ref": "Dashboard.load",
 "payload": {"points": [[0, 12, 30, 4],
                        [1, 18, 28, 5],
                        [2, 22, 31, 7]]}}

// reconfigure series + colours (typical use: redraw with a new shape)
{"op": "write", "ref": "Dashboard.load",
 "payload": {"series": ["a", "b"], "colors": ["#2563eb", "#16a34a"],
             "points": [[0, 1, 2], [1, 3, 4]]}}

// toggle stacked / overlay
{"op": "write", "ref": "Dashboard.load", "payload": {"stacked": false}}

// labels
{"op": "write", "ref": "Dashboard.load",
 "payload": {"x_label": "tick", "y_label": "load"}}

// switch to time mode
{"op": "write", "ref": "Dashboard.load", "payload": {"x_format": "time"}}

// clear
{"op": "write", "ref": "Dashboard.load", "payload": {"points": []}}

// one new row -- one x, three y's, matching `series` order
{"op": "append", "ref": "Dashboard.load", "payload": [42, 21, 33, 9]}
```

Single-series degenerate case (`series = ["value"]`):

```
// replace
{"op": "write", "ref": "P.area", "payload": {"points": [[0, 1], [1, 4], [2, 9]]}}
// append
{"op": "append", "ref": "P.area", "payload": [3, 16]}
```

Payload is a msgpack map for `write` and an array for `append`. Nu sentinels on any y encode as msgpack nil; on the browser nil becomes a gap in that series' area (`connectNulls={false}`). A nil x falls back to the row's index inside the new buffer.

Wire representation rule: stacked vs not, single vs many -- it is always a single `points` field whose rows are `[x, y0, y1, ...]` with one y per entry in `series`. There is no per-series append op and no nested list-of-series. The renderer fans out per-series at paint time.

## renderer

`web/src/refs/area-chart.tsx`. recharts `AreaChart` inside a `ResponsiveContainer` at `h-64 w-full`. Rows are transformed into recharts data objects keyed by series name: `{x, [series_0]: y0, [series_1]: y1, ...}`. One `<Area>` per entry in `series`, in order, with `stroke = color`, `fill = color`, `fillOpacity = 0.25`, `dot = false`, `isAnimationActive = false`, `connectNulls = false`. When `stacked` is true every `<Area>` shares `stackId="s"`. When `x_format === "time"` x ticks and tooltip labels render as `HH:MM:SS`. A light `CartesianGrid` and a `Tooltip` are drawn; a `Legend` shows when `series.length > 1`. No shadcn dep.

## slice shape

```
{
  type: "AreaChart",
  value: { points: [[x, y0, y1, ...], ...] },   // raw rows; same shape as the wire
  series: string[],
  colors: string[],
  stacked: boolean,
  x_label: string,
  y_label: string,
  max_points: number,
  x_format: "number" | "time",
  write: (v: partial) => void,
  append: (v: [x, ...ys]) => void,
}
```

Seeded from `field.props` on mount. `write` merges the partial payload and, when `max_points` shrinks or `series.length` changes, re-normalises the existing buffer (trim tail, pad missing y's with `null`, drop extras). `append` pushes one row and drops the oldest once length exceeds `max_points`. The renderer derives recharts-shaped data from `value.points + series` at render time -- the buffer itself is not duplicated per-series.

## edge cases

- empty `write` payload (`{}`): no-op.
- `points` row shorter than `1 + len(series)`: missing y's stored as `null` (gaps).
- `points` row longer than `1 + len(series)`: extras dropped.
- `points` rows with non-numeric x: x falls back to the row's index in the buffer.
- `points` rows with non-numeric or NaN y: that y stored as `null`, drawn as a gap.
- `series` changed with `points` absent: existing rows kept; per-row y-list re-shaped to the new length (truncate or null-pad on the right). callers can call `store_series` alone to add a slot, then `append` fresh rows.
- `colors` shorter than `series`: cycle. longer: extras ignored.
- `colors` non-list or contains non-strings: those entries skipped, cycle continues.
- `stacked` non-bool: coerced (`Boolean(v)`).
- `max_points <= 0` or non-numeric: clamped to `1`.
- `max_points` shrinks below buffer length: tail-trim immediately.
- `x_format` unknown string or nil: falls back to `"number"`.
- `append` row length mismatched against `series`: pad with `null` or truncate as in `write`.
- `append` payload not an array or length < 1: no-op for the push.
- `append` when slice missing: no-op.
- empty `series = []`: rendered as an empty chart (axes only). `append` is a no-op (no y slots).

## non-goals

- no per-series append op. one `append` row carries every series.
- no per-series `write` -- the buffer is a single rows table, not a dict of named series.
- no brush, zoom, or pan.
- no client-side downsampling beyond the sliding window cap.
- no read / notify ops. server pushes only.
- no curve type switch (always `monotone`).
- no separate stroke vs fill colour. one colour per series; fill alpha is fixed at 0.25.
- no percent-stacked / normalised mode. `stacked` is plain additive stacking.
