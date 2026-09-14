// TableRef -- tabular data with columns and positional rows.
//
// Server-owned data. `columns` and `rows` are plain props now, side by side
// with the chrome, so the old {columns, rows} composite under `value` is
// gone. Three ops the default cannot do on its own:
//
//   write   a partial merge, same as the default, except `max_rows` is a
//           sliding window: oldest rows drop on overflow.
//   append  push a single row, same cap.
//   read    answer {columns, rows}, which is what the old slice `value` was
//           and therefore what the old default read shipped back.
//
// Shapes of cells and columns are normalized at read time, in the view.
//
// Sort is server-driven: the browser shows arrows on the active column and
// emits a notify {sort_column, sort_direction} when a header is clicked.
// The server decides whether to re-sort and confirms via set_sort.
//
// When clickable_rows is true, body rows hover and emit a notify
// {row_index} on click. The browser does not select or mutate locally.
//
// Composes the kit Table primitive family; density maps striped to
// primitive's `striped` variant and dense to `compact`. Sort arrows are
// lucide chevrons.

import { OPS, type Props } from "@nustackdev/ui-core";
import { ChevronDown, ChevronUp } from "lucide-react";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "../../components/ui/table";
import { Text } from "../../components/ui/text";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useListProp,
	useSend,
	useStringProp,
} from "../../tree";

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

function _maxRows(props: Props): number {
	const n = Number(props.max_rows);
	return Number.isFinite(n) ? Math.max(0, Math.floor(n)) : 0;
}

function TableView({ path }: NodeProps) {
	const rawColumns = useListProp<unknown>(path, "columns");
	const rawRows = useListProp<unknown>(path, "rows");
	const striped = useBoolProp(path, "striped", true);
	const dense = useBoolProp(path, "dense");
	const sortColumn = useStringProp(path, "sort_column");
	const sortDirection = useStringProp(path, "sort_direction", "asc") === "desc" ? "desc" : "asc";
	const clickableRows = useBoolProp(path, "clickable_rows");
	const send = useSend(path);
	const rows = _rows(rawRows);
	let cols = _strings(rawColumns);
	if (cols.length === 0 && rows.length > 0) {
		const width = rows.reduce((m, r) => Math.max(m, Array.isArray(r) ? r.length : 0), 0);
		cols = Array.from({ length: width }, (_, i) => `col_${i}`);
	}
	if (rows.length === 0 && cols.length === 0) {
		return (
			<Text size="sm" tone="muted">
				no rows
			</Text>
		);
	}
	const density = dense ? "compact" : "default";
	const variant = striped ? "striped" : "default";
	const colSlots = cols.map((c, i) => ({ id: `${i}:${c}`, label: c, idx: i }));

	function onHeaderClick(col: string) {
		const nextDir = col === sortColumn && sortDirection === "asc" ? "desc" : "asc";
		send(OPS.notify, { sort_column: col, sort_direction: nextDir });
	}

	function onRowClick(i: number) {
		if (!clickableRows) return;
		send(OPS.notify, { row_index: i });
	}

	return (
		<Table variant={variant} density={density}>
			<TableHeader>
				<TableRow>
					{colSlots.map((c) => {
						const active = c.label === sortColumn && c.label !== "";
						return (
							<TableHead
								key={c.id}
								scope="col"
								aria-sort={
									active ? (sortDirection === "desc" ? "descending" : "ascending") : "none"
								}
								className="cursor-pointer select-none data-[active=true]:text-text-primary"
								data-active={active || undefined}
								onClick={() => onHeaderClick(c.label)}
							>
								<span className="inline-flex items-center gap-1">
									{c.label}
									{active ? (
										sortDirection === "desc" ? (
											<ChevronDown className="size-3.5" />
										) : (
											<ChevronUp className="size-3.5" />
										)
									) : null}
								</span>
							</TableHead>
						);
					})}
				</TableRow>
			</TableHeader>
			<TableBody>
				{rows.map((r, i) => {
					const row = Array.isArray(r) ? r : [];
					const rowKey = `row-${i}`;
					return (
						<TableRow
							key={rowKey}
							onClick={() => onRowClick(i)}
							className={clickableRows ? "cursor-pointer" : undefined}
						>
							{colSlots.map((c) => (
								<TableCell key={c.id}>{_cell(row[c.idx])}</TableCell>
							))}
						</TableRow>
					);
				})}
			</TableBody>
		</Table>
	);
}

export const TableRef: NodeEntry = {
	component: TableView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				if (payload == null || typeof payload !== "object" || Array.isArray(payload)) return;
				const p = payload as Record<string, unknown>;
				Object.assign(props, p);
				if ("rows" in p) props.rows = _cap(_rows(p.rows), _maxRows(props));
			}),
		append: (ctx, payload) =>
			ctx.update((props) => {
				if (!Array.isArray(payload)) return;
				props.rows = _cap([..._rows(props.rows), payload], _maxRows(props));
			}),
		read: (ctx) =>
			ctx.send(
				OPS.read,
				{ columns: _strings(ctx.node.props.columns), rows: _rows(ctx.node.props.rows) },
				ctx.frame.id,
			),
	},
};
