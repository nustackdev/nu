// TableRef -- tabular data with columns and positional rows.
//
// Server-owned. `write` carries a partial `{columns?, rows?}` map; missing
// keys leave the slice as is. `append` pushes a single row. A `max_rows`
// cap on the slice acts as a sliding window: oldest rows drop on overflow.
// Class-level defaults arrive on the mount field's `props` and seed the
// slice (columns, striped, dense, maxRows).

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

type Table = { columns: string[]; rows: unknown[][] };

function _cell(v: unknown): string {
	if (v == null) return "";
	if (typeof v === "object") return JSON.stringify(v);
	return String(v);
}

function _strings(v: unknown): string[] {
	if (!Array.isArray(v)) return [];
	return v.map((c) => (c == null ? "" : String(c)));
}

function _rows(v: unknown): unknown[][] {
	if (!Array.isArray(v)) return [];
	return v.filter((r): r is unknown[] => Array.isArray(r));
}

function _cap(rows: unknown[][], maxRows: number): unknown[][] {
	if (maxRows > 0 && rows.length > maxRows) {
		return rows.slice(rows.length - maxRows);
	}
	return rows;
}

const factory: SliceFactory = (path, ctx, props) => {
	const initialColumns = _strings(props?.columns);
	const striped = typeof props?.striped === "boolean" ? (props.striped as boolean) : true;
	const dense = typeof props?.dense === "boolean" ? (props.dense as boolean) : false;
	const maxRows =
		typeof props?.max_rows === "number" && Number.isFinite(props.max_rows)
			? Math.max(0, Math.floor(props.max_rows as number))
			: 0;
	return {
		type: "TableRef",
		value: { columns: initialColumns, rows: [] } as Table,
		striped,
		dense,
		maxRows,
		write: (v) =>
			ctx.set((refs) => {
				const slice = refs[path];
				if (!slice) return;
				const p = (v ?? {}) as { columns?: unknown; rows?: unknown };
				const cur = slice.value as Table;
				const next: Table = {
					columns: "columns" in p ? _strings(p.columns) : cur.columns,
					rows: "rows" in p ? _cap(_rows(p.rows), slice.maxRows as number) : cur.rows,
				};
				slice.value = next;
			}),
		append: (v) =>
			ctx.set((refs) => {
				const slice = refs[path];
				if (!slice) return;
				if (!Array.isArray(v)) return;
				const cur = slice.value as Table;
				const next = cur.rows.concat([v as unknown[]]);
				slice.value = {
					columns: cur.columns,
					rows: _cap(next, slice.maxRows as number),
				};
			}),
	};
};

function TableView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as Table | undefined);
	const striped = useStore((s) => (s.refs[path]?.striped as boolean) ?? true);
	const dense = useStore((s) => (s.refs[path]?.dense as boolean) ?? false);
	const rows = Array.isArray(value?.rows) ? value.rows : [];
	let cols = Array.isArray(value?.columns) ? value.columns : [];
	if (cols.length === 0 && rows.length > 0) {
		const width = rows.reduce((m, r) => Math.max(m, Array.isArray(r) ? r.length : 0), 0);
		cols = Array.from({ length: width }, (_, i) => `col_${i}`);
	}
	if (rows.length === 0 && cols.length === 0) {
		return <div className="text-sm text-gray-500 italic">no rows</div>;
	}
	const cellPad = dense ? "px-2 py-0.5" : "px-2 py-1";
	// Stable per-column keys: column ids may repeat, so we attach the slot
	// index to disambiguate without using bare array index as the key.
	const colSlots = cols.map((c, i) => ({ id: `${i}:${c}`, label: c, idx: i }));
	return (
		<div className="w-full overflow-auto">
			<table className="w-full text-sm font-mono">
				<thead>
					<tr className="border-b border-gray-300 bg-gray-50 text-left">
						{colSlots.map((c) => (
							<th key={c.id} className={`${cellPad} font-medium`}>
								{c.label}
							</th>
						))}
					</tr>
				</thead>
				<tbody>
					{rows.map((r, i) => {
						const row = Array.isArray(r) ? r : [];
						const rowKey = `row-${i}`;
						const zebra = striped && i % 2 === 1 ? "bg-gray-50/50" : "";
						return (
							<tr key={rowKey} className={`border-b border-gray-100 ${zebra}`}>
								{colSlots.map((c) => (
									<td key={c.id} className={cellPad}>
										{_cell(row[c.idx])}
									</td>
								))}
							</tr>
						);
					})}
				</tbody>
			</table>
		</div>
	);
}

export const TableRef: RefEntry = { factory, component: TableView };
