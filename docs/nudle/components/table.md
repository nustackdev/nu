# TableRef

Tabular data with explicit columns and positional rows. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field      | type        | default | notes                                                            |
| ---------- | ----------- | ------- | ---------------------------------------------------------------- |
| `columns`  | `list[str]` | `[]`    | initial header. empty means "infer from first row's length".     |
| `striped`  | `bool`      | `True`  | alternate row backgrounds in the body.                           |
| `dense`    | `bool`      | `False` | tighter vertical padding on body cells.                          |
| `max_rows` | `int`       | `0`     | sliding window cap on the rows buffer. `0` disables the cap.     |

Declared as plain class attributes on the python `TableRef`. They ship once on `mount` under the field entry's `props` key and seed the browser slice (no explicit `write` needed). `columns` lands on `slice.value.columns`; `striped`, `dense`, and `max_rows` live as top-level slice fields (`striped`, `dense`, `maxRows`).

## interactions

| op       | dir           | payload                                            | nu method        | notes                                                            |
| -------- | ------------- | -------------------------------------------------- | ---------------- | ---------------------------------------------------------------- |
| `write`  | server -> tab | `{"columns"?: [str], "rows"?: [[cell, ...], ...]}` | `store`, `clear` | partial; keys absent from the payload leave the slice as is.     |
| `append` | server -> tab | `[cell, ...]` (single row)                         | `append`         | row pushed onto the buffer; capped by `max_rows` (sliding).      |

Three nu methods compile to two wire ops:

- `store(table)` -> `write table` -- `table` is `{"columns"?: [...], "rows"?: [[...], ...]}`. Either key may be omitted.
- `clear()` -> `write {"rows": []}` -- empties the rows buffer; keeps the current columns.
- `append(row)` -> `append row` -- `row` is a list of cells aligned to the current columns.

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "HomePage.tbl", "type": "TableRef",
 "props": {"columns": [], "striped": true, "dense": false, "max_rows": 0}}

// full-table write
{"op": "write", "ref": "HomePage.tbl",
 "payload": {"columns": ["id", "name"], "rows": [[1, "a"], [2, "b"]]}}

// rows-only write (header preserved from earlier write or props)
{"op": "write", "ref": "HomePage.tbl", "payload": {"rows": [[3, "c"]]}}

// clear
{"op": "write", "ref": "HomePage.tbl", "payload": {"rows": []}}

// append one row
{"op": "append", "ref": "HomePage.tbl", "payload": [4, "d"]}
```

Payload of `write` is a msgpack map. Missing keys mean "keep current slice value". Cells may be any msgpack-encodable value; Nu sentinels (EMPTY / INVALID) encode as msgpack nil and render as the empty string.

## renderer

`web/src/refs/table.tsx`. A plain `<table>` with a sticky-style header row (`bg-gray-50`, bottom border) and body rows. When `striped` is true, odd-indexed body rows get a subtle background (`bg-gray-50/50`). When `dense` is true, body cells switch from `py-1` to `py-0.5`. Cells stringify scalars and JSON-stringify objects; nil renders as `""`. If the buffer is empty (no rows and no columns) the renderer shows a "no rows" placeholder.

If columns are not declared (neither on `props` nor on any `write`), the header is inferred from the widest current row as `col_0, col_1, ...`. When both columns and rows are empty, no header is rendered.

## slice shape

```
{
  type: "TableRef",
  value: { columns: string[], rows: unknown[][] },
  striped: boolean,
  dense: boolean,
  maxRows: number,
  write: (v: {columns?, rows?}) => void,
  append: (row: unknown[]) => void,
}
```

Seeded from `field.props` on mount. `write` merges incoming partial payloads into `value`; `append` pushes one row and applies the sliding-window cap.

## edge cases

- empty `write` payload (`{}`): no-op, slice unchanged.
- `columns` is msgpack nil or non-list: treated as absent.
- `rows` non-list: treated as `[]` for that write.
- a row inside `rows` that is not a list: dropped.
- `append` with a non-list payload: dropped (no error frame).
- `max_rows == 0`: no cap, buffer grows unbounded.
- `max_rows > 0` and `write` larger than the cap: only the last `max_rows` rows are kept.
- `append` overflow: oldest rows drop until length `<= max_rows`.
- cell that is `null` / `undefined`: rendered as `""`.
- cell that is an object or array: rendered via `JSON.stringify`.
- columns shorter than a row: extra cells are not rendered.
- columns longer than a row: missing cells render as `""`.
- `clear()` while the table has no rows: still emits a write with `{"rows": []}`; slice rewrites the array.

## non-goals

- no per-cell click / hover, no row selection, no sorting, no filtering.
- no `notify`. fully display-only.
- no column typing or right-alignment for numerics in v0.
- no virtualization; `max_rows` is the only buffer cap.
- no `read`.
