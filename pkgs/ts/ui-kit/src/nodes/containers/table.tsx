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
//   columns   one record per column, the one the DataTable takes too:
//             {key?, label?, width?, min_width?, max_width?, wrap?,
//             hide_below?, align?}. The header row draws each `label` (the
//             key when there is none); a header cell with content
//             (`t.header[c]`, the "header" row's child c) draws that
//             instead. No labels and no header row: no header. Widths are
//             lengths (a number is px), `wrap` "wrap" | "nowrap" |
//             "truncate", `hide_below` px of the table's width under which
//             the column is not drawn, `align` "start" | "center" | "end".
//   variant   "default" (framed) | "borderless" | "striped".
//   density   "compact" | "default" | "comfortable" (rows 24 / 28 / 32).
//   label     the table's accessible name, "Table" by default.
//   span      {"r,c": {cols, rows}}: the cell at row r, column c covers that
//             many columns and rows, and the cells under it are not drawn.
//             "header,c" spans header cells (columns only). `set_child`
//             ({key, span}) changes one entry, as on a Grid.
//   width, min_width, max_width, height, min_height, max_height, scroll
//             the size layer, on the box around the table's frame.
//
// A hidden row (`t[r].hide()`) draws nothing and keeps its place number; a
// hidden cell draws an empty cell.

import { getNode, type Path } from "@nustackdev/ui-core";
import { useMemo, useState } from "react";
import { useShallow } from "zustand/react/shallow";
import {
	COLUMN_ALIGN,
	COLUMN_ITEMS,
	type ColumnAlign,
	ColumnBox,
	type ColumnLayout,
	columnCellStyle,
	columnHeadStyle,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	Table as TablePrimitive,
	TableRow as TableRowPrimitive,
	useHiddenColumns,
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
	useProps,
	useStringProp,
	useTree,
} from "../../tree";
import {
	childHandlers,
	cssLength,
	readSpans,
	SCROLL_CLASSES,
	type Scroll,
	type Span,
	sizeStyle,
} from "./layout";

/** The segment the header row sits at; body rows are digits, so it never collides. */
const HEADER = "header";

const VARIANTS = ["default", "borderless", "striped"] as const;
const DENSITIES = ["compact", "default", "comfortable"] as const;
const ALIGNS: readonly ColumnAlign[] = ["start", "center", "end"];
const WRAPS = ["wrap", "nowrap", "truncate"] as const;

const isIndex = (s: string) => /^\d+$/.test(s);

/** A column as the table draws it: its label, and how it lays out. */
type Column = ColumnLayout & { label: string; align: ColumnAlign };

/** The `columns` records off the wire; anything that is not a record is skipped. */
export function readColumns(raw: readonly unknown[]): Column[] {
	const out: Column[] = [];
	for (const c of raw) {
		if (c == null || typeof c !== "object" || Array.isArray(c)) continue;
		const d = c as Record<string, unknown>;
		const label = d.label ?? d.key;
		out.push({
			label: label == null ? "" : String(label),
			align: ALIGNS.find((a) => a === d.align) ?? "start",
			width: cssLength(d.width),
			minWidth: cssLength(d.min_width),
			maxWidth: cssLength(d.max_width),
			wrap: WRAPS.find((w) => w === d.wrap),
			hideBelow: typeof d.hide_below === "number" ? d.hide_below : undefined,
		});
	}
	return out;
}

const PLAIN: Column = { label: "", align: "start" };

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
function CellContent({ path, col }: { path: Path; col: Column }) {
	const { type, props } = useNode(path);
	const hidden = useHidden(path);
	if (hidden || type === null) return null;
	const view = <NodeView path={path} />;
	const title = typeof props.value === "string" ? props.value : undefined;
	return (
		<FlowProvider flow="block">
			<ColumnBox col={col} title={title}>
				{isFill(type, props) ? (
					view
				) : (
					<div
						data-slot="table-place"
						className={cn("flex min-w-0 flex-col", COLUMN_ITEMS[col.align])}
					>
						{view}
					</div>
				)}
			</ColumnBox>
		</FlowProvider>
	);
}

type RowProps = {
	path: Path;
	row: string;
	cols: number;
	columns: readonly Column[];
	hiddenCols: ReadonlySet<number>;
	covered: Set<string>;
	spanAt: Map<string, Span>;
};

function BodyRow({ path, row, cols, columns, hiddenCols, covered, spanAt }: RowProps) {
	const rowPath = useMemo(() => [...path, row], [path, row]);
	const hidden = useHidden(rowPath);
	if (hidden) return null;
	const cells = [];
	for (let c = 0; c < cols; c++) {
		const key = `${row},${c}`;
		if (covered.has(key)) continue;
		const span = spanAt.get(key);
		const col = columns[c] ?? PLAIN;
		cells.push(
			<TableCell
				key={c}
				colSpan={span && span.cols > 1 ? span.cols : undefined}
				rowSpan={span && span.rows > 1 ? span.rows : undefined}
				className={COLUMN_ALIGN[col.align]}
				style={columnCellStyle(hiddenCols.has(c))}
			>
				<CellContent path={[...rowPath, String(c)]} col={col} />
			</TableCell>,
		);
	}
	return <TableRowPrimitive data-row={row}>{cells}</TableRowPrimitive>;
}

function HeaderRow({ path, cols, columns, hiddenCols, covered, spanAt }: Omit<RowProps, "row">) {
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
		const col = columns[c] ?? PLAIN;
		cells.push(
			<TableHead
				key={c}
				colSpan={span && span.cols > 1 ? span.cols : undefined}
				className={COLUMN_ALIGN[col.align]}
				style={columnHeadStyle(col, hiddenCols.has(c))}
			>
				{written.includes(String(c)) ? (
					<CellContent path={[...rowPath, String(c)]} col={col} />
				) : (
					col.label
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
	const rawColumns = useListProp<unknown>(path, "columns");
	const rawSpans = useProp<unknown>(path, "span", null);
	const props = useProps(path);
	const { width, min_width, max_width, height, min_height, max_height, scroll } = props;
	const size = useMemo(
		() => sizeStyle({ width, min_width, max_width, height, min_height, max_height }),
		[width, min_width, max_width, height, min_height, max_height],
	);
	const [frame, setFrame] = useState<HTMLDivElement | null>(null);
	const [rows, written] = useExtent(path);
	const headerShown = useTree((s) => {
		const node = getNode(s.root, [...path, HEADER]);
		return node != null && !node.hidden;
	});
	const columns = useMemo(() => readColumns(rawColumns), [rawColumns]);
	const hiddenCols = useHiddenColumns(frame, columns);
	const labelled = columns.some((c) => c.label !== "");
	const cols = Math.max(written, columns.length);
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
				columns={columns}
				hiddenCols={hiddenCols}
				covered={covered}
				spanAt={spanAt}
			/>,
		);
	}

	return (
		<div
			ref={setFrame}
			data-slot="table-box"
			className={cn("min-w-0", typeof scroll === "string" && SCROLL_CLASSES[scroll as Scroll])}
			style={size}
		>
			<TablePrimitive aria-label={label} variant={variant} density={density}>
				{labelled || headerShown ? (
					<TableHeader>
						<HeaderRow
							path={path}
							cols={cols}
							columns={columns}
							hiddenCols={hiddenCols}
							covered={covered}
							spanAt={spanAt}
						/>
					</TableHeader>
				) : null}
				<TableBody>{body}</TableBody>
			</TablePrimitive>
		</div>
	);
}

/** A row drawn outside a Table (it never should be): its cells, one after another. */
function TableRowView({ path }: NodeProps) {
	return <NodeChildren path={path} indexed />;
}

export const Table: NodeEntry = {
	component: TableView,
	fill: true,
	// `set_child` {key, span}: one cell's span merged into the map, 1 by 1 drops it.
	handlers: { ...childHandlers },
};

export const TableRow: NodeEntry = { component: TableRowView };
