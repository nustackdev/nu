// TableRef -- rows and columns on the kit DataTable: reads by default, and
// selects, edits, inserts, deletes and moves rows when the server asks it to.
//
// Server-owned rows, browser-owned moment. The server ships `columns` and
// `rows` as plain props; which rows are selected the browser keeps in its own
// `selected` prop as you click, and a server write overrides it: one copy,
// whoever wrote last wins. The browser never edits the rows. An edit, an
// insert, a delete or a move is a request the server answers by shipping the
// rows as they now are; a request it turns down leaves the table as it was.
//
// ## Props
//
//   columns         a list; a string is `{key: s}`, a dict is
//                   `{key, label?, kind?, options?, editable?, align?, width?, sortable?}`
//                   with kind "text" | "number" | "bool" | "select". Strings and dicts mix.
//                   No columns and some rows: positional `col_0..`, or the dict rows' keys.
//   rows            a list; a list is cells by column position, a dict is cells by column key.
//   row_key         the field that keys a row: a column key for list rows, any field for
//                   dict rows, shown or not (see "Row keys").
//   label           the grid's accessible name, "Table" by default.
//   striped         true by default; `dense` picks the compact density.
//   max_rows        a sliding window on write and append: the oldest rows drop on overflow.
//   sort_column, sort_direction   the arrows; the server sorts, the browser only shows it.
//   clickable_rows  rows point and a click (or Enter on a cell that does not edit) notifies.
//   selection       "none" | "single" | "multi"; `selected` is the list of selected keys.
//                   Keys of rows no longer shown drop out of it (written back, no notify).
//   editable        every column edits unless its dict says `editable: false`; the
//                   `row_key` column never does.
//   addable, deletable, draggable   insert, delete and move rows (keyboard, menu, drag).
//
// Every header sorts unless its dict says `sortable: false`, as it always has.
//
// ## Row keys
//
// Without `row_key` a row's key is its position as a string, and the
// selection the browser keeps follows positions, not rows. So set `row_key`
// whenever rows can be inserted, deleted, moved or re-sorted. Its values must
// be unique: a duplicate gets "~2", "~3", ... in order so the grid still
// works, and that suffixed key is what events carry. A row whose key is
// missing or empty falls back to its index, which may collide with a real
// key, so give every row one. Every event that names rows by key also names
// them by position (`row_index`, `row_indexes`), so a table without
// `row_key` is still fully usable.
//
// ## Notifies
//
// One notify per intent on the table's own path, the intent named in `event`
// (the server's `on_*` each take one):
//
//   {event: "sort", sort_column, sort_direction}             a header; confirm with set_sort
//   {event: "row", row_index, key}                           needs clickable_rows
//   {event: "select", keys, row_indexes}             the whole next selection; needs selection
//   {event: "edit", key, row_index, column, value, previous}  value typed by kind; needs editable
//   {event: "add", index}                            a new row at index; needs addable
//   {event: "delete", keys, row_indexes}             needs deletable
//   {event: "move", key, row_index, index}           index counts rows without key; needs draggable
//
// `row_indexes` runs parallel to `keys`. Every position (`row_index`,
// `row_indexes`, the add and move `index`) counts within the rows shown, which
// under `max_rows` are the newest ones only. Columns in a notify are as the
// server sent them (`column` is the column's key, `sort_column` too).
//
// ## Handlers
//
//   write   a partial merge, except `max_rows` is a sliding window over `rows`.
//   append  push one row (a list or a dict), same cap.
//   patch   one row-level change, named in `op`, so the server ships only what changed:
//             {op: "set_row", key, row}     replace the row keyed `key` in place, or
//                                           append it when no row has that key (same cap)
//             {op: "insert_row", index, row}  insert at index, clamped to the rows (same cap)
//             {op: "remove_rows", keys}     drop the rows with these keys
//             {op: "set_order", keys}       these rows first, in this order; the rest keep
//                                           their order after them; unknown keys skipped
//           Keys are the ones the grid draws (see "Row keys", suffixes included), the first
//           row with a key is the one touched, and a malformed patch changes nothing.
//   read    answer {columns, rows} as they were sent.

import { OPS, type Props } from "@nustackdev/ui-core";
import { useCallback, useEffect, useMemo } from "react";
import {
	DataTable,
	type DataTableColumn,
	type DataTableEdit,
	type DataTableKind,
	type DataTableRow,
} from "../../components/ui/data-table";
import { Text } from "../../components/ui/text";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useListProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

type WireRow = unknown[] | Record<string, unknown>;

/** A column as drawn: the kit's shape under a key unique in the table, plus the key as sent. */
type Column = DataTableColumn & { name: string };

const KINDS: readonly DataTableKind[] = ["text", "number", "bool", "select"];
const ALIGNS = ["left", "center", "right"] as const;
const NO_KEYS: string[] = [];

function str(v: unknown): string {
	return v == null ? "" : String(v);
}

function isDict(v: unknown): v is Record<string, unknown> {
	return v != null && typeof v === "object" && !Array.isArray(v);
}

function readRows(v: unknown): WireRow[] {
	if (!Array.isArray(v)) return [];
	return v.filter((r): r is WireRow => Array.isArray(r) || isDict(r));
}

function cap(rows: WireRow[], maxRows: number): WireRow[] {
	if (maxRows > 0 && rows.length > maxRows) {
		return rows.slice(rows.length - maxRows);
	}
	return rows;
}

function maxRowsOf(props: Props): number {
	const n = Number(props.max_rows);
	return Number.isFinite(n) ? Math.max(0, Math.floor(n)) : 0;
}

/** The columns as `read` answers them: strings as before, dicts as sent. */
function sentColumns(v: unknown): unknown[] {
	if (!Array.isArray(v)) return [];
	return v.map((c) => (isDict(c) ? c : str(c)));
}

/** "~2", "~3", ... after a key already taken, so every key is unique and stable in order. */
function unique(key: string, taken: Set<string>): string {
	let out = key;
	for (let n = 2; taken.has(out); n++) out = `${key}~${n}`;
	taken.add(out);
	return out;
}

/** The wire's columns as the kit draws them; positional or dict-row keys when none are sent. */
function readColumns(
	raw: readonly unknown[],
	rows: readonly WireRow[],
	rowKey: string,
	editable: boolean,
): Column[] {
	const specs: Record<string, unknown>[] = raw.map((c) => (isDict(c) ? c : { key: str(c) }));
	if (specs.length === 0 && rows.length > 0) {
		const first = rows.find(isDict);
		if (first) {
			const names = new Set<string>();
			for (const r of rows) if (isDict(r)) for (const k of Object.keys(r)) names.add(k);
			for (const k of names) specs.push({ key: k });
		} else {
			const width = rows.reduce((m, r) => Math.max(m, Array.isArray(r) ? r.length : 0), 0);
			for (let i = 0; i < width; i++) specs.push({ key: `col_${i}` });
		}
	}
	const taken = new Set<string>();
	return specs.map((d) => {
		const name = str(d.key);
		const kind = KINDS.includes(d.kind as DataTableKind) ? (d.kind as DataTableKind) : "text";
		const align = ALIGNS.find((a) => a === d.align);
		return {
			key: unique(name, taken),
			name,
			label: d.label == null ? name : str(d.label),
			kind,
			options: Array.isArray(d.options) ? d.options.map(str) : undefined,
			editable: editable && d.editable !== false && (rowKey === "" || name !== rowKey),
			align,
			width: d.width == null ? undefined : str(d.width),
			sortable: d.sortable !== false,
		};
	});
}

/** The wire's rows as the kit draws them: cells by column, each under a unique key. */
function readTableRows(rows: readonly WireRow[], cols: readonly Column[], rowKey: string) {
	const keyAt = rowKey === "" ? -1 : cols.findIndex((c) => c.name === rowKey);
	const taken = new Set<string>();
	return rows.map((r, i): DataTableRow => {
		const list = Array.isArray(r);
		const cells = cols.map((c, j) => (list ? r[j] : r[c.name]));
		const own = rowKey === "" ? "" : str(list ? (keyAt >= 0 ? r[keyAt] : undefined) : r[rowKey]);
		return { key: unique(own === "" ? String(i) : own, taken), cells };
	});
}

/** The keys the grid draws for these rows under the node's props, in row order. */
function keysOf(rows: readonly WireRow[], props: Props): string[] {
	const rowKey = str(props.row_key);
	const raw = Array.isArray(props.columns) ? props.columns : [];
	const cols = readColumns(raw, rows, rowKey, false);
	return readTableRows(rows, cols, rowKey).map((r) => r.key);
}

/** A key as a patch names it: a string, or a number by its digits. */
function keyArg(v: unknown): string | null {
	if (typeof v === "string") return v;
	if (typeof v === "number" && Number.isFinite(v)) return String(v);
	return null;
}

function keyList(v: unknown): string[] | null {
	if (!Array.isArray(v)) return null;
	return v.map(keyArg).filter((k): k is string => k !== null);
}

function isRow(v: unknown): v is WireRow {
	return Array.isArray(v) || isDict(v);
}

/** The rows after one patch, or null when the patch is malformed or unknown. */
function patched(
	rows: WireRow[],
	keys: readonly string[],
	patch: Record<string, unknown>,
	maxRows: number,
): WireRow[] | null {
	switch (patch.op) {
		case "set_row": {
			const key = keyArg(patch.key);
			const row = patch.row;
			if (key === null || !isRow(row)) return null;
			const at = keys.indexOf(key);
			if (at < 0) return cap([...rows, row], maxRows);
			const next = [...rows];
			next[at] = row;
			return next;
		}
		case "insert_row": {
			const index = patch.index;
			const row = patch.row;
			if (typeof index !== "number" || !Number.isFinite(index) || !isRow(row)) return null;
			const at = Math.min(Math.max(0, Math.floor(index)), rows.length);
			return cap([...rows.slice(0, at), row, ...rows.slice(at)], maxRows);
		}
		case "remove_rows": {
			const drop = keyList(patch.keys);
			if (drop === null) return null;
			const gone = new Set(drop);
			return rows.filter((_, i) => !gone.has(keys[i]));
		}
		case "set_order": {
			const order = keyList(patch.keys);
			if (order === null) return null;
			const placed = new Set<number>();
			const first: WireRow[] = [];
			for (const key of order) {
				const at = keys.indexOf(key);
				if (at < 0 || placed.has(at)) continue;
				placed.add(at);
				first.push(rows[at]);
			}
			return [...first, ...rows.filter((_, i) => !placed.has(i))];
		}
		default:
			return null;
	}
}

function TableView({ path }: NodeProps) {
	const rawColumns = useListProp<unknown>(path, "columns");
	const rawRows = useListProp<unknown>(path, "rows");
	const rawSelected = useListProp<unknown>(path, "selected");
	const label = useStringProp(path, "label", "Table");
	const rowKey = useStringProp(path, "row_key");
	const striped = useBoolProp(path, "striped", true);
	const dense = useBoolProp(path, "dense");
	const sortColumn = useStringProp(path, "sort_column");
	const sortDirection = useStringProp(path, "sort_direction", "asc") === "desc" ? "desc" : "asc";
	const clickableRows = useBoolProp(path, "clickable_rows");
	const selectionProp = useStringProp(path, "selection", "none");
	const selection =
		selectionProp === "single" || selectionProp === "multi" ? selectionProp : "none";
	const editable = useBoolProp(path, "editable");
	const addable = useBoolProp(path, "addable");
	const deletable = useBoolProp(path, "deletable");
	const draggable = useBoolProp(path, "draggable");
	const setProps = useSetProps(path);
	const send = useSend(path);

	const wireRows = useMemo(() => readRows(rawRows), [rawRows]);
	const cols = useMemo(
		() => readColumns(rawColumns, wireRows, rowKey, editable),
		[rawColumns, wireRows, rowKey, editable],
	);
	const rows = useMemo(() => readTableRows(wireRows, cols, rowKey), [wireRows, cols, rowKey]);
	const indexOf = useMemo(() => new Map(rows.map((r, i) => [r.key, i])), [rows]);
	// Only keys of rows still shown: a row that went away leaves the selection
	// with it, so no event ever names a row the server already dropped.
	const selected = useMemo(() => {
		const keys = rawSelected.map(str).filter((k) => indexOf.has(k));
		return keys.length ? keys : NO_KEYS;
	}, [rawSelected, indexOf]);
	useEffect(() => {
		if (selected.length !== rawSelected.length) setProps({ selected });
	}, [selected, rawSelected, setProps]);
	const indexes = useCallback(
		(keys: readonly string[]) => keys.map((k) => indexOf.get(k) ?? -1),
		[indexOf],
	);
	const sortKey = cols.find((c) => c.name === sortColumn && sortColumn !== "")?.key;
	const nameOf = useCallback((key: string) => cols.find((c) => c.key === key)?.name ?? key, [cols]);

	const notify = useCallback(
		(event: string, fields: Record<string, unknown>) => send(OPS.notify, { event, ...fields }),
		[send],
	);

	const onSort = useCallback(
		(column: string, direction: "asc" | "desc") =>
			notify("sort", { sort_column: nameOf(column), sort_direction: direction }),
		[notify, nameOf],
	);

	const onActivate = useCallback(
		(key: string, index: number) => notify("row", { row_index: index, key }),
		[notify],
	);

	const onSelect = useCallback(
		(keys: string[]) => {
			setProps({ selected: keys });
			notify("select", { keys, row_indexes: indexes(keys) });
		},
		[setProps, notify, indexes],
	);

	const onEdit = useCallback(
		(e: DataTableEdit) =>
			notify("edit", {
				key: e.key,
				row_index: e.index,
				column: nameOf(e.column),
				value: e.value,
				previous: e.previous,
			}),
		[notify, nameOf],
	);

	const onAdd = useCallback((index: number) => notify("add", { index }), [notify]);
	const onDelete = useCallback(
		(keys: string[]) => notify("delete", { keys, row_indexes: indexes(keys) }),
		[notify, indexes],
	);
	const onMove = useCallback(
		(key: string, index: number) =>
			notify("move", { key, index, row_index: indexOf.get(key) ?? -1 }),
		[notify, indexOf],
	);

	if (rows.length === 0 && cols.length === 0) {
		return (
			<Text size="sm" tone="muted">
				no rows
			</Text>
		);
	}

	return (
		<DataTable
			aria-label={label}
			columns={cols}
			rows={rows}
			density={dense ? "compact" : "default"}
			striped={striped}
			sort={sortKey ? { column: sortKey, direction: sortDirection } : null}
			onSort={onSort}
			selection={selection}
			selected={selected}
			onSelect={selection !== "none" ? onSelect : undefined}
			onActivate={clickableRows ? onActivate : undefined}
			onEdit={cols.some((c) => c.editable) ? onEdit : undefined}
			onAdd={addable ? onAdd : undefined}
			onDelete={deletable ? onDelete : undefined}
			onMove={draggable ? onMove : undefined}
			className={clickableRows ? "[&_tbody_tr]:cursor-pointer" : undefined}
		/>
	);
}

export const TableRef: NodeEntry = {
	component: TableView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				if (!isDict(payload)) return;
				Object.assign(props, payload);
				if ("rows" in payload) props.rows = cap(readRows(payload.rows), maxRowsOf(props));
			}),
		append: (ctx, payload) =>
			ctx.update((props) => {
				if (!Array.isArray(payload) && !isDict(payload)) return;
				props.rows = cap([...readRows(props.rows), payload], maxRowsOf(props));
			}),
		patch: (ctx, payload) =>
			ctx.update((props) => {
				if (!isDict(payload)) return;
				const rows = readRows(props.rows);
				const next = patched(rows, keysOf(rows, props), payload, maxRowsOf(props));
				if (next) props.rows = next;
			}),
		read: (ctx) =>
			ctx.send(
				OPS.read,
				{ columns: sentColumns(ctx.node.props.columns), rows: readRows(ctx.node.props.rows) },
				ctx.frame.id,
			),
	},
};
