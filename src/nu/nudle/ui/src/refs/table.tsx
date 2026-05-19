// TableRef -- rows of dicts. Header is the union of every row's keys.
//
// Rows can carry holes: a cell may be `null` when the server resolved a
// Ref to a Nu sentinel (EMPTY / INVALID). The renderer treats any
// non-object row or null cell as blank rather than throwing.

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

type Row = Record<string, unknown>;

function _toRows(v: unknown): Row[] {
	if (!Array.isArray(v)) return [];
	return v.filter((r): r is Row => !!r && typeof r === "object" && !Array.isArray(r));
}

function _cell(v: unknown): string {
	if (v == null) return "";
	if (typeof v === "object") return JSON.stringify(v);
	return String(v);
}

const factory: SliceFactory = (path, ctx) => ({
	type: "TableRef",
	value: [] as Row[],
	write: (v) =>
		ctx.set((refs) => {
			refs[path].value = _toRows(v);
		}),
});

function TableView({ path }: { path: string }) {
	// Select the stored value (a stable reference -- `write` already
	// normalized it). Normalizing inside the selector would mint a new
	// array every render and spin an infinite update loop.
	const value = useStore((s) => s.refs[path]?.value);
	const rows = _toRows(value);
	if (rows.length === 0) {
		return <div className="text-sm text-gray-500 italic">no rows</div>;
	}
	// Union of keys: a sparse first row must not drop later columns.
	const cols = Array.from(new Set(rows.flatMap((r) => Object.keys(r))));
	return (
		<div className="w-full overflow-auto">
			<table className="w-full text-sm font-mono">
				<thead>
					<tr className="border-b border-gray-300 text-left">
						{cols.map((c) => (
							<th key={c} className="px-2 py-1">
								{c}
							</th>
						))}
					</tr>
				</thead>
				<tbody>
					{rows.map((r, i) => {
						const rowKey = (r.mint ?? r.id ?? `row-${i}`) as string;
						return (
							<tr key={rowKey} className="border-b border-gray-100">
								{cols.map((c) => (
									<td key={c} className="px-2 py-1">
										{_cell(r[c])}
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
