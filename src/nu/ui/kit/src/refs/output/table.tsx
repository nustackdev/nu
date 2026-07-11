// TableRef -- tabular data with columns and positional rows.
//
// Server-owned data. `write` carries a partial map of
// {columns?, rows?, sort_column?, sort_direction?}; missing keys leave the
// slice as is. `append` pushes a single row. A `max_rows` cap on the slice
// acts as a sliding window: oldest rows drop on overflow. Class-level
// defaults arrive on the mount field's `props` and seed the slice.
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

import { ChevronDown, ChevronUp } from "lucide-react";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "../../components/ui/table";
import { Text } from "../../components/ui/text";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

type TableValue = { columns: string[]; rows: unknown[][] };

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

function _dir(v: unknown): "asc" | "desc" {
	return v === "desc" ? "desc" : "asc";
}

const factory: SliceFactory = (path, ctx, props) => {
	const initialColumns = _strings(props?.columns);
	const striped = typeof props?.striped === "boolean" ? (props.striped as boolean) : true;
	const dense = typeof props?.dense === "boolean" ? (props.dense as boolean) : false;
	const maxRows =
		typeof props?.max_rows === "number" && Number.isFinite(props.max_rows)
			? Math.max(0, Math.floor(props.max_rows as number))
			: 0;
	const sortColumn = typeof props?.sort_column === "string" ? (props.sort_column as string) : "";
	const sortDirection = _dir(props?.sort_direction);
	const clickableRows =
		typeof props?.clickable_rows === "boolean" ? (props.clickable_rows as boolean) : false;
	return {
		type: "TableRef",
		value: { columns: initialColumns, rows: [] } as TableValue,
		striped,
		dense,
		maxRows,
		sortColumn,
		sortDirection,
		clickableRows,
		write: (v) =>
			ctx.set((refs) => {
				const slice = refs[path];
				if (!slice) return;
				const p = (v ?? {}) as {
					columns?: unknown;
					rows?: unknown;
					sort_column?: unknown;
					sort_direction?: unknown;
				};
				const cur = slice.value as TableValue;
				const next: TableValue = {
					columns: "columns" in p ? _strings(p.columns) : cur.columns,
					rows: "rows" in p ? _cap(_rows(p.rows), slice.maxRows as number) : cur.rows,
				};
				slice.value = next;
				if ("sort_column" in p) {
					slice.sortColumn = p.sort_column == null ? "" : String(p.sort_column);
				}
				if ("sort_direction" in p) {
					slice.sortDirection = _dir(p.sort_direction);
				}
			}),
		append: (v) =>
			ctx.set((refs) => {
				const slice = refs[path];
				if (!slice) return;
				if (!Array.isArray(v)) return;
				const cur = slice.value as TableValue;
				const next = cur.rows.concat([v as unknown[]]);
				slice.value = {
					columns: cur.columns,
					rows: _cap(next, slice.maxRows as number),
				};
			}),
	};
};

function TableView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as TableValue | undefined);
	const striped = useStore((s) => (s.refs[path]?.striped as boolean) ?? true);
	const dense = useStore((s) => (s.refs[path]?.dense as boolean) ?? false);
	const sortColumn = useStore((s) => (s.refs[path]?.sortColumn as string) ?? "");
	const sortDirection = useStore((s) => (s.refs[path]?.sortDirection as string) ?? "asc");
	const clickableRows = useStore((s) => Boolean(s.refs[path]?.clickableRows));
	const send = useStore((s) => s.send);
	const rows = Array.isArray(value?.rows) ? value.rows : [];
	let cols = Array.isArray(value?.columns) ? value.columns : [];
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
		send({
			op: OP_NOTIFY,
			ref: path,
			payload: { sort_column: col, sort_direction: nextDir },
		});
	}

	function onRowClick(i: number) {
		if (!clickableRows) return;
		send({ op: OP_NOTIFY, ref: path, payload: { row_index: i } });
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

export const TableRef: RefEntry = { factory, component: TableView };
