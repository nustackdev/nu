---
title: TableRef
---

Tabular data with explicit columns and positional rows. Server-owned. Display by default; opt in to sortable headers and row clicks.

## kind

display (+ optional notify)

## defaults (class-level)

| field            | type        | default | notes                                                                |
| ---------------- | ----------- | ------- | -------------------------------------------------------------------- |
| `columns`        | `list[str]` | `[]`    | initial header. empty means "infer from first row's length".         |
| `striped`        | `bool`      | `True`  | alternate row backgrounds in the body.                               |
| `dense`          | `bool`      | `False` | tighter vertical padding on body cells.                              |
| `max_rows`       | `int`       | `0`     | sliding window cap on the rows buffer. `0` disables the cap.         |
| `sort_column`    | `str`       | `""`    | which column id is sorted. empty means unsorted.                     |
| `sort_direction` | `str`       | `"asc"` | `"asc"` or `"desc"`. only meaningful when `sort_column` is non-empty.|
| `clickable_rows` | `bool`      | `False` | when true, body rows hover and emit a row-click notify.              |

Declared as plain class attributes on the python `TableRef`. They ship once on `mount` under the field entry's `props` key and seed the browser slice (no explicit `write` needed). `columns` lands on `slice.value.columns`; the rest live as top-level slice fields (`striped`, `dense`, `maxRows`, `sortColumn`, `sortDirection`, `clickableRows`).

## interactions

| op       | dir           | payload                                                                       | nu method                         | notes                                                                                  |
| -------- | ------------- | ----------------------------------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------- |
| `write`  | server -> tab | `{"columns"?, "rows"?, "sort_column"?, "sort_direction"?}`                    | `store`, `clear`, `store_sort`    | partial; keys absent from the payload leave the slice as is.                           |
| `append` | server -> tab | `[cell, ...]` (single row)                                                    | `append`                          | row pushed onto the buffer; capped by `max_rows` (sliding).                            |
| `notify` | tab -> server | `{"sort_column": str, "sort_direction": "asc"\|"desc"}` or `{"row_index": int}` | `row_clicked` (subscribe)        | header click and row click share the same notify channel; differentiate by payload shape. |

Nu methods compile to wire ops:

- `set(table)` -> `write table` -- `table` is `{"columns"?: [...], "rows"?: [[...], ...]}`.
- `clear()` -> `write {"rows": []}` -- empties the rows buffer; keeps the current columns.
- `append(row)` -> `append row` -- row is a list of cells aligned to current columns.
- `store_sort(column, direction)` -> `write {"sort_column": column, "sort_direction": direction}` -- confirm the active sort on the browser (does not re-sort data; the server is expected to issue a fresh `store` with sorted rows if it wants the data reordered).
- `row_clicked()` -> Subscription. Receives raw notify payloads; the callback should branch on shape (`row_index` vs `sort_column`). Wire-level subscription identical to `ButtonRef.clicked()`.

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "HomePage.tbl", "type": "TableRef",
 "props": {"columns": [], "striped": true, "dense": false, "max_rows": 0,
           "sort_column": "", "sort_direction": "asc", "clickable_rows": false}}

// full-table write
{"op": "write", "ref": "HomePage.tbl",
 "payload": {"columns": ["id", "name"], "rows": [[1, "a"], [2, "b"]]}}

// confirm active sort
{"op": "write", "ref": "HomePage.tbl",
 "payload": {"sort_column": "id", "sort_direction": "desc"}}

// browser -> server: user clicked a header
{"op": "notify", "ref": "HomePage.tbl",
 "payload": {"sort_column": "id", "sort_direction": "asc"}}

// browser -> server: user clicked a row (clickable_rows = true)
{"op": "notify", "ref": "HomePage.tbl", "payload": {"row_index": 3}}
```

Payload of `write` is a msgpack map. Missing keys mean "keep current slice value". Cells may be any msgpack-encodable value; Nu sentinels (EMPTY / INVALID) encode as msgpack nil and render as the empty string.

## renderer

`web/src/refs/table.tsx`. A plain `<table>` with a header row (`bg-gray-50`, bottom border) and body rows. When `striped` is true, odd-indexed body rows get a subtle background. When `dense` is true, body cells switch to tighter padding.

Header cells are clickable. The active column carries a trailing arrow (`↑` for asc, `↓` for desc). Clicking the active column toggles direction; clicking a different column emits asc for that column. The renderer does not mutate the slice on click -- it only sends the notify. Local sort state lives in the slice and is updated by the server's confirming `store_sort` write.

When `clickable_rows` is true, body rows get a `hover:bg-gray-100 cursor-pointer` style and emit `{row_index: i}` on click. When false, rows have no hover and no click handler effect.

If columns are not declared (neither on `props` nor on any `write`), the header is inferred from the widest current row as `col_0, col_1, ...`. When both columns and rows are empty, no header is rendered.

## slice shape

```
{
  type: "TableRef",
  value: { columns: string[], rows: unknown[][] },
  striped: boolean,
  dense: boolean,
  maxRows: number,
  sortColumn: string,
  sortDirection: "asc" | "desc",
  clickableRows: boolean,
  write: (v: {columns?, rows?, sort_column?, sort_direction?}) => void,
  append: (row: unknown[]) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into `value` and into the top-level sort fields; `append` pushes one row and applies the sliding-window cap.

## sort flow (server is the source of truth)

1. Server mounts the table with `sort_column=""` (or some default) and `sort_direction="asc"`.
2. Server issues `set(table)` with rows in whatever order it likes.
3. User clicks a header. Browser emits a notify `{sort_column, sort_direction}`. No local data is reordered.
4. Server receives the notify (via a subscription, e.g. `Changed(table)` or a `row_clicked()` callback that branches on payload shape).
5. Server decides whether to honor the request. If yes, it issues a fresh `set(table_sorted)` with reordered rows, then `store_sort(column, direction)` to confirm the active state on the browser (or fold both into one write payload that carries `rows`, `sort_column`, `sort_direction` together).

## edge cases

- empty `write` payload (`{}`): no-op, slice unchanged.
- `columns`, `rows`, `sort_column`, `sort_direction` individually absent: that field is left as is.
- `sort_direction` not equal to `"asc"` or `"desc"`: coerced to `"asc"`.
- `sort_column` set to a value not present in `columns`: arrow disappears (no header matches), but the slice still holds the value.
- `clickable_rows == false` and a row click happens: no notify is sent (the renderer's handler short-circuits).
- header click while `clickable_rows == true` does not also fire the row click (the `<th>` is in `<thead>`, not in body rows).
- `max_rows == 0`: no cap, buffer grows unbounded.
- `append` overflow: oldest rows drop until length `<= max_rows`.
- cell that is `null` / `undefined`: rendered as `""`.
- cell that is an object or array: rendered via `JSON.stringify`.
- columns shorter than a row: extra cells are not rendered.
- columns longer than a row: missing cells render as `""`.

## non-goals

- no client-side sorting. the browser never reorders rows; sort is purely a header-state hint plus a notify.
- no per-cell click, no column drag, no resize, no row selection (clickable_rows is a single-shot notify, not a selection model).
- no filtering, no pagination.
- no column typing or right-alignment for numerics in v0.
- no virtualization; `max_rows` is the only buffer cap.
- no `read`.
