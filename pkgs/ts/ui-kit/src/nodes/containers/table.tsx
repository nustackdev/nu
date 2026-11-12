// Table -- a content table: rows and columns of places, any content in each.
//
// The Python `TableRef`. Its children are rows (`TableRow`), keyed by
// position ("0", "1", ...) plus "header" for the header row; a row's children
// are its cells, keyed by column position. Any kind sits in a cell: a text, a
// badge, a row of buttons, a card, another table. Rows and cells draw in
// number order whatever order they were written in, and every position up to
// the largest written one gets a row and a cell, empty when nothing is there,
// so `t[2, 3]` alone is the fourth cell of the third row.
//
// Rows that are data (sort, select, edit, live row ops) are the other table,
// `DataTableRef`; this one has no behavior of its own. It draws on the kit
// Table primitive, so it looks like the data table and a markdown table.
//
// ## Props
//
//   header    the header row's labels, by column. A header cell with content
//             (`t.header[c]`, the "header" row's child c) draws that instead.
//             No labels and no header row: no header.
//   align     each column's alignment, "left" | "center" | "right", by position.
//   variant   "default" (framed) | "borderless" | "striped".
//   density   "compact" | "default" | "comfortable" (rows 24 / 28 / 32).
//   label     the table's accessible name, "Table" by default.
//   spans     {"r,c": {cols, rows}}: the cell at row r, column c covers that
//             many columns and rows, and the cells under it are not drawn.
//             "header,c" spans header cells (columns only). `set_span` is its
//             own op ({key, cols, rows}), merged here, as on a Grid.
//
// A hidden row (`t[r].hide()`) draws nothing and keeps its place number; a
// hidden cell draws an empty cell.

import { getNode, type Path } from "@nustackdev/ui-core";
import { useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import {
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	Table as TablePrimitive,
	TableRow as TableRowPrimitive,
} from "../../components/ui/table";
import { cn } from "../../lib/utils";
import {
	FlowProvider,
	isFill,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	NodeView,
	useEnumProp,
	useHidden,
	useListProp,
	useNode,
	useProp,
	useStringProp,
	useTree,
} from "../../tree";
import { readSpans } from "./grid";

/** The segment the header row sits at; body rows are digits, so it never collides. */
const HEADER = "header";

const VARIANTS = ["default", "borderless", "striped"] as const;
const DENSITIES = ["compact", "default", "comfortable"] as const;
type Align = "left" | "center" | "right";
const ALIGNS: readonly Align[] = ["left", "center", "right"];

const TEXT_ALIGN: Record<Align, string> = {
	left: "text-left",
	center: "text-center",
	right: "text-right",
};
const ITEMS: Record<Align, string> = {
	left: "items-start",
	center: "items-center",
	right: "items-end",
};

const isIndex = (s: string) => /^\d+$/.test(s);

type Span = { cols: number; rows: number };

/**
 * How many body rows and columns there are: one past the largest position
 * written, hidden ones included so a hidden row keeps its number.
 */
function useExtent(path: Path): [number, number] {
	return useTree(
		useShallow((s) => {
			const node = getNode(s.root, path);
			let rows = 0;
			let cols = 0;
			if (!node) return [rows, cols];
			for (const [segment, row] of node.children) {
				if (isIndex(segment)) rows = Math.max(rows, Number(segment) + 1);
				else if (segment !== HEADER) continue;
				for (const cell of row.children.keys()) {
					if (isIndex(cell)) cols = Math.max(cols, Number(cell) + 1);
				}
			}
			return [rows, cols];
		}),
	);
}

/**
 * Which cells a span covers, as "r,c" keys, and the span each origin draws
 * with. A span is clipped to the table, so it never reaches past the last row
 * or column.
 */
function layout(
	spans: Record<string, Span>,
	rows: number,
	cols: number,
): { covered: Set<string>; spanAt: Map<string, Span> } {
	const covered = new Set<string>();
	const spanAt = new Map<string, Span>();
	for (const [key, span] of Object.entries(spans)) {
		const [r, c] = key.split(",");
		if (c === undefined || !isIndex(c)) continue;
		const col = Number(c);
		const header = r === HEADER;
		if (!header && !isIndex(r)) continue;
		const row = header ? 0 : Number(r);
		const width = Math.max(1, Math.min(span.cols, cols - col));
		const height = header ? 1 : Math.max(1, Math.min(span.rows, rows - row));
		spanAt.set(key, { cols: width, rows: height });
		for (let dr = 0; dr < height; dr++) {
			for (let dc = 0; dc < width; dc++) {
				if (dr === 0 && dc === 0) continue;
				covered.add(`${header ? HEADER : row + dr},${col + dc}`);
			}
		}
	}
	return { covered, spanAt };
}

/**
 * What a cell holds, aligned as its column says. A fill child (a chart, an
 * input, a card) takes the cell's width; anything else keeps its own width at
 * the column's edge. A hidden child leaves the cell empty.
 */
function CellContent({ path, align }: { path: Path; align: Align }) {
	const { type, props } = useNode(path);
	const hidden = useHidden(path);
	if (hidden || type === null) return null;
	const view = <NodeView path={path} />;
	return (
		<FlowProvider flow="block">
			{isFill(type, props) ? (
				view
			) : (
				<div data-slot="table-place" className={cn("flex min-w-0 flex-col", ITEMS[align])}>
					{view}
				</div>
			)}
		</FlowProvider>
	);
}

type RowProps = {
	path: Path;
	row: string;
	cols: number;
	aligns: readonly Align[];
	covered: Set<string>;
	spanAt: Map<string, Span>;
};

function BodyRow({ path, row, cols, aligns, covered, spanAt }: RowProps) {
	const rowPath = useMemo(() => [...path, row], [path, row]);
	const hidden = useHidden(rowPath);
	if (hidden) return null;
	const cells = [];
	for (let c = 0; c < cols; c++) {
		const key = `${row},${c}`;
		if (covered.has(key)) continue;
		const span = spanAt.get(key);
		const align = aligns[c] ?? "left";
		cells.push(
			<TableCell
				key={c}
				colSpan={span && span.cols > 1 ? span.cols : undefined}
				rowSpan={span && span.rows > 1 ? span.rows : undefined}
				className={TEXT_ALIGN[align]}
			>
				<CellContent path={[...rowPath, String(c)]} align={align} />
			</TableCell>,
		);
	}
	return <TableRowPrimitive data-row={row}>{cells}</TableRowPrimitive>;
}

function HeaderRow({
	path,
	labels,
	cols,
	aligns,
	covered,
	spanAt,
}: Omit<RowProps, "row"> & { labels: readonly unknown[] }) {
	const rowPath = useMemo(() => [...path, HEADER], [path]);
	const written = useTree(
		useShallow((s) => {
			const node = getNode(s.root, rowPath);
			return node ? [...node.children.keys()] : [];
		}),
	);
	const cells = [];
	for (let c = 0; c < cols; c++) {
		const key = `${HEADER},${c}`;
		if (covered.has(key)) continue;
		const span = spanAt.get(key);
		const align = aligns[c] ?? "left";
		const label = labels[c];
		cells.push(
			<TableHead
				key={c}
				colSpan={span && span.cols > 1 ? span.cols : undefined}
				className={TEXT_ALIGN[align]}
			>
				{written.includes(String(c)) ? (
					<CellContent path={[...rowPath, String(c)]} align={align} />
				) : label == null ? (
					""
				) : (
					String(label)
				)}
			</TableHead>,
		);
	}
	return <TableRowPrimitive>{cells}</TableRowPrimitive>;
}

function TableView({ path }: NodeProps) {
	const variant = useEnumProp(path, "variant", VARIANTS, "default");
	const density = useEnumProp(path, "density", DENSITIES, "default");
	const label = useStringProp(path, "label", "Table");
	const labels = useListProp<unknown>(path, "header");
	const rawAligns = useListProp<unknown>(path, "align");
	const rawSpans = useProp<unknown>(path, "spans", null);
	const [rows, written] = useExtent(path);
	const headerShown = useTree((s) => {
		const node = getNode(s.root, [...path, HEADER]);
		return node != null && !node.hidden;
	});
	const cols = Math.max(written, labels.length);
	const aligns = useMemo(
		() => rawAligns.map((a) => (ALIGNS.includes(a as Align) ? (a as Align) : "left")),
		[rawAligns],
	);
	// Span hook: the same {cols, rows} map a Grid reads, keyed "r,c".
	const { covered, spanAt } = useMemo(
		() => layout(readSpans(rawSpans), rows, cols),
		[rawSpans, rows, cols],
	);

	const body = [];
	for (let r = 0; r < rows; r++) {
		body.push(
			<BodyRow
				key={r}
				path={path}
				row={String(r)}
				cols={cols}
				aligns={aligns}
				covered={covered}
				spanAt={spanAt}
			/>,
		);
	}

	return (
		<TablePrimitive aria-label={label} variant={variant} density={density}>
			{labels.length > 0 || headerShown ? (
				<TableHeader>
					<HeaderRow
						path={path}
						labels={labels}
						cols={cols}
						aligns={aligns}
						covered={covered}
						spanAt={spanAt}
					/>
				</TableHeader>
			) : null}
			<TableBody>{body}</TableBody>
		</TablePrimitive>
	);
}

/** A row drawn outside a Table (it never should be): its cells, one after another. */
function TableRowView({ path }: NodeProps) {
	return <NodeChildren path={path} indexed />;
}

export const Table: NodeEntry = {
	component: TableView,
	fill: true,
	handlers: {
		// One cell's span merged into the map, as Grid's set_span: 1 by 1 drops it.
		set_span: (ctx, payload) =>
			ctx.update((props) => {
				const p = (payload ?? {}) as Record<string, unknown>;
				const key = p.key == null ? "" : String(p.key);
				if (key === "") return;
				const spans = { ...readSpans(props.spans) };
				const next = readSpans({ [key]: { cols: p.cols, rows: p.rows } })[key];
				if (next) spans[key] = next;
				else delete spans[key];
				props.spans = spans;
			}),
	},
};

export const TableRow: NodeEntry = { component: TableRowView };
