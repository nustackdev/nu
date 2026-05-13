// TableRef -- rows of dicts. Header derived from the first row's keys.

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

type Row = Record<string, unknown>;

const factory: SliceFactory = (path, ctx) => ({
	type: "TableRef",
	value: [] as Row[],
	write: (v) =>
		ctx.set((refs) => {
			refs[path].value = (v as Row[]) ?? [];
		}),
});

function TableView({ path }: { path: string }) {
	const rows = useStore((s) => (s.refs[path]?.value as Row[] | undefined) ?? []);
	if (rows.length === 0) {
		return <div className="text-sm text-gray-500 italic">no rows</div>;
	}
	const cols = Object.keys(rows[0]);
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
										{String(r[c] ?? "")}
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
