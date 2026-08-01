---
title: BarChart
---

Categorical bar chart. Display-only, server-owned. recharts on the browser.

## kind

display

## defaults (class-level)

| field         | type                                | default      | notes                                                                |
| ------------- | ----------------------------------- | ------------ | -------------------------------------------------------------------- |
| `x_label`     | `str`                               | `""`         | X axis label; empty hides it                                         |
| `y_label`     | `str`                               | `""`         | Y axis label; empty hides it                                         |
| `color`       | `str`                               | `"#2563eb"`  | bar fill colour (any css colour string)                              |
| `orientation` | `Literal["vertical", "horizontal"]` | `"vertical"` | `"vertical"` -> bars rise on Y; `"horizontal"` -> bars extend on X   |
| `max_bars`    | `int`                               | `200`        | cap on bar count; oldest categories drop when buffer goes over       |

Declared as plain class attributes on the python `BarChart`. They ship on `mount` under the field entry's `props` key and seed the browser slice without an explicit `write`. `bars` itself is not a class default; it starts as `[]` in the slice until the server writes / appends.

## interactions

| op       | dir           | payload                                                                                                                       | nu method                                                                                                                              | notes                                                                          |
| -------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `write`  | server -> tab | `{"bars"?: [[category, value], ...], "x_label"?: str, "y_label"?: str, "color"?: str, "orientation"?: str, "max_bars"?: int}` | `store`, `store_bars`, `store_x_label`, `store_y_label`, `store_color`, `store_orientation`, `store_max_bars`, `clear`                 | partial update; absent keys leave the slice as is.                             |
| `append` | server -> tab | `[category, value]`                                                                                                           | `append`                                                                                                                                | upserts one bar by category; if category exists, value is replaced in place.   |

Nu methods compile to the same wire ops with different payload subsets:

- `store_bars(seq)` -> `write {"bars": seq}`
- `store_x_label(t)` / `store_y_label(t)` -> `write {"x_label" | "y_label": t}`
- `store_color(c)` -> `write {"color": c}`
- `store_orientation(name)` -> `write {"orientation": name}`
- `store_max_bars(n)` -> `write {"max_bars": n}`
- `set(bars, x_label=..., y_label=..., color=..., orientation=..., max_bars=...)` -> `write` of the present keys
- `clear()` -> `write {"bars": []}` (convenience; not a new op)
- `append(category, value)` -> `append [category, value]`

Legacy / shape tolerance on `bars`: `set({"bars": [...]})` (first positional arg a dict) still works; the dict is unwrapped. A flat list of values `[v0, v1, ...]` is accepted and auto-categorised to `"0".."n-1"`. A list of `{label, value}` maps is also accepted.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "Dashboard.totals", "type": "BarChart",
 "props": {"x_label": "", "y_label": "", "color": "#2563eb",
           "orientation": "vertical", "max_bars": 200}}

// replace series
{"op": "write", "ref": "Dashboard.totals",
 "payload": {"bars": [["jan", 12], ["feb", 19], ["mar", 7]]}}

// labels + colour
{"op": "write", "ref": "Dashboard.totals",
 "payload": {"x_label": "month", "y_label": "count", "color": "#16a34a"}}

// switch to horizontal layout
{"op": "write", "ref": "Dashboard.totals", "payload": {"orientation": "horizontal"}}

// clear
{"op": "write", "ref": "Dashboard.totals", "payload": {"bars": []}}

// one new bar (upsert by category)
{"op": "append", "ref": "Dashboard.totals", "payload": ["apr", 4]}
```

Payload is a msgpack map (for `write`) or a 2-array (for `append`). A bar's `value` may decode to nil (Nu sentinel); on the browser nil becomes `null` and renders as a gap (the bar is dropped from the dataset, the category label stays). `category` is coerced to string; nil category falls back to its index.

## renderer

`web/src/refs/bar-chart.tsx`. recharts `BarChart` inside a `ResponsiveContainer` at `h-64 w-full`. When `orientation === "vertical"`: category axis is `XAxis` (`dataKey="x"`), value axis is `YAxis`. When `orientation === "horizontal"`: chart `layout="vertical"`, `XAxis type="number"`, `YAxis type="category" dataKey="x"`. Bar fill uses `color`. Light `CartesianGrid` for readability. `Tooltip` enabled. No external shadcn dep. No animation (`isAnimationActive={false}`).

## slice shape

```
{
  type: "BarChart",
  value: { bars: [[category: string, value: number | null], ...] },
  x_label: string,
  y_label: string,
  color: string,
  orientation: "vertical" | "horizontal",
  max_bars: number,
  write: (v: partial) => void,
  append: (v: [category, value]) => void,
}
```

Seeded from `field.props` on mount. `write` merges the partial payload and, when `max_bars` shrinks, tail-trims the existing buffer. `append` upserts by category: if the category exists, its value is replaced in place; otherwise the pair is pushed and the oldest entry drops once length exceeds `max_bars`.

## edge cases

- empty `write` payload (`{}`): no-op, slice unchanged.
- `bars` with non-string category: coerced via `String(...)`; nil category falls back to its index.
- `bars` with non-numeric or NaN value: stored as `null`, drawn as a gap (no bar, label remains).
- `max_bars <= 0` or non-numeric: clamped to `1`.
- `max_bars` shrinks below current buffer length: tail-trim immediately.
- `orientation` unknown string or nil: falls back to `"vertical"`.
- `color` non-string or nil: keeps current value.
- flat value list on `write.bars`: auto-categorised to `"0".."n-1"`.
- list-of-maps `[{label, value}, ...]` on `write.bars`: normalised to pairs.
- `append` when slice missing: no-op.
- `append` with a non-2-array payload: no-op for the push (slice still re-trims).
- duplicate categories in a `write.bars` list: last write wins per category (later entries replace earlier).

## non-goals

- no stacked or grouped bars. one value per category.
- no per-bar colour overrides. single `color` for the whole series.
- no client-side sort (server controls order).
- no zoom, brush, or legend.
- no read / notify ops. server pushes only.
