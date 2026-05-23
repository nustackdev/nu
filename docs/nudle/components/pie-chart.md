# PieChart

Pie / donut chart built from a list of `(label, value)` slices. Display-only, server-owned. recharts on the browser.

## kind

display

## defaults (class-level)

| field          | type        | default     | notes                                                                                   |
| -------------- | ----------- | ----------- | --------------------------------------------------------------------------------------- |
| `slices`       | `list`      | `[]`        | initial slices; each is `[label: str, value: float]`. seeded into the slice on mount.   |
| `colors`       | `list[str]` | see below   | per-slice palette; cycles when there are more slices than colors.                       |
| `inner_radius` | `float`     | `0.0`       | donut hole as a fraction in `[0, 1)` of the outer radius. `0.0` = pie, `> 0` = donut.   |
| `show_labels`  | `bool`      | `True`      | draw slice labels on the chart.                                                         |
| `show_legend`  | `bool`      | `True`      | draw recharts `Legend` below the chart.                                                 |
| `total_label`  | `str`       | `""`        | text shown in the center of the donut; empty hides it. ignored when `inner_radius == 0`.|

Default palette:
`["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2", "#db2777", "#65a30d"]`.

Declared as plain class attributes on the python `PieChart`. They ship on `mount` under the field entry's `props` key and seed the browser slice without an explicit `write`.

## interactions

| op       | dir           | payload                                                                                                                                              | nu method                                                                                                                              | notes                                                  |
| -------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `write`  | server -> tab | `{"slices"?: [[label, value], ...], "colors"?: [str, ...], "inner_radius"?: float, "show_labels"?: bool, "show_legend"?: bool, "total_label"?: str}` | `store`, `store_slices`, `store_colors`, `store_inner_radius`, `store_show_labels`, `store_show_legend`, `store_total_label`, `clear`  | partial update; absent keys leave the slice as is.     |
| `append` | server -> tab | `[label, value]`                                                                                                                                     | `append`                                                                                                                               | pushes one slice. no cap.                              |

Nu methods compile to the same wire ops with different payload subsets:

- `store_slices(seq)` -> `write {"slices": seq}`
- `store_colors(seq)` -> `write {"colors": seq}`
- `store_inner_radius(f)` -> `write {"inner_radius": f}`
- `store_show_labels(b)` / `store_show_legend(b)` -> `write {"show_labels" | "show_legend": b}`
- `store_total_label(t)` -> `write {"total_label": t}`
- `store(slices=..., colors=..., inner_radius=..., show_labels=..., show_legend=..., total_label=...)` -> `write` of the present keys
- `clear()` -> `write {"slices": []}` (convenience; not a new op)
- `append(label, value)` -> `append [label, value]`

Legacy parity with LineChart: `store({"slices": [...]})` (first positional arg a dict containing `slices`) unwraps to `{"slices": ...}`. A flat `[v0, v1, ...]` on `slices` is accepted and auto-labeled to `"0".."n-1"` strings.

## wire payloads

```
// mount field entry (inside the mount payload)
{"path": "Dashboard.spending", "type": "PieChart",
 "props": {"slices": [], "colors": ["#2563eb", "#16a34a", "#f59e0b", "#dc2626",
                                    "#7c3aed", "#0891b2", "#db2777", "#65a30d"],
           "inner_radius": 0.0, "show_labels": true, "show_legend": true,
           "total_label": ""}}

// replace slices
{"op": "write", "ref": "Dashboard.spending",
 "payload": {"slices": [["rent", 1200], ["food", 450], ["transit", 80]]}}

// switch to donut + center label
{"op": "write", "ref": "Dashboard.spending",
 "payload": {"inner_radius": 0.55, "total_label": "monthly"}}

// custom palette
{"op": "write", "ref": "Dashboard.spending",
 "payload": {"colors": ["#16a34a", "#f59e0b", "#dc2626"]}}

// hide legend
{"op": "write", "ref": "Dashboard.spending", "payload": {"show_legend": false}}

// clear
{"op": "write", "ref": "Dashboard.spending", "payload": {"slices": []}}

// one new slice
{"op": "append", "ref": "Dashboard.spending", "payload": ["other", 35.5]}
```

Payload is a msgpack map (for `write`) or a 2-array (for `append`). Each slice on the wire is a 2-array `[label, value]`: label is a string, value is a finite float `>= 0`. Nu sentinels on `value` encode as msgpack nil; the browser stores nil as `0` so the slice contributes nothing to the pie.

## renderer

`web/src/refs/pie-chart.tsx`. recharts `PieChart` inside a `ResponsiveContainer` at `h-64 w-full`. One `Pie` element with `dataKey="value"` and `nameKey="label"`; `outerRadius="80%"` and `innerRadius = round(inner_radius * 80) + "%"`. Each slice gets a `<Cell fill={colors[i % colors.length]} />`. `Tooltip` is always on; `Legend` only when `show_legend === true`. Slice labels render via the `Pie`'s `label` prop only when `show_labels === true`. When `inner_radius > 0` and `total_label` is non-empty, a centered `<g>` element shows the label on top and the slice total below. `isAnimationActive={false}` for parity with LineChart. No external shadcn dep.

## slice shape

```
{
  type: "PieChart",
  value: { slices: [{ label: string, value: number }, ...] },
  colors: string[],
  inner_radius: number,      // clamped to [0, 0.95]
  show_labels: boolean,
  show_legend: boolean,
  total_label: string,
  write: (v: partial) => void,
  append: (v: [label, value]) => void,
}
```

Seeded from `field.props` on mount. The wire form `[label, value]` is converted to `{label, value}` on receive. `write` merges the partial payload; `append` pushes one slice.

## edge cases

- empty `write` payload (`{}`): no-op, slice unchanged.
- empty `slices` (`[]`): chart renders the empty container; recharts handles no-data.
- slice with non-string label: coerced via `String(label)`.
- slice with non-numeric, NaN, or negative value: stored as `0` (contributes nothing).
- Nu sentinel on slice value (msgpack nil): stored as `0`.
- `inner_radius` out of range or non-numeric: clamped to `[0, 0.95]`; nil falls back to `0`.
- `colors` non-list, empty, or all non-string: falls back to the default palette.
- `colors` shorter than `slices`: palette cycles by `i % colors.length`.
- `show_labels` / `show_legend` non-bool: falls back to the default (`true`).
- `total_label` non-string: keeps current value.
- `append` when slice missing: no-op.
- `append` with a non-2-array payload: no-op.
- flat numeric array on `write.slices`: auto-labeled to `"0".."n-1"`.

## non-goals

- no multi-pie / nested-pie (sunburst).
- no click-to-select or hover-explode slices; no notify / read ops.
- no animation tuning beyond `isAnimationActive={false}`.
- no percent vs absolute toggle in tooltip; recharts default is the value.
- no client-side sorting of slices by value; the server is the source of order.
