// Grid -- children in cells: equal cells that flow, or places on a board.
//
// Children are its own, in the tree, one cell each. Composes
// the kit Grid primitive, which owns the track list: `max_columns` caps the
// cells on a row (0 lets the width decide), `min_cell_width` is the
// narrowest a cell gets, so the same grid is three wide on a desktop and
// stacks on a phone.
//
// Each child sits in a cell box that hands it a "grid" flow and fills it:
// the child stretches to the cell's width, and to the row's height when
// `align` is "stretch", so a row of cards lines up whatever each one holds.
//
// The grid itself has no intrinsic width, so its entry declares `fill`: in a
// Row it takes a share of the free width instead of its content's size.
//
// Layout (`layout.tsx`): the size props, `padding` (0), `gap` (4), `justify`
// (stretch) places a cell's child across its track, `align` (stretch) down
// it. Per child, keyed by segment: `span` ({cols, rows}) and `align_self`.
// The child carries nothing, so the same Card is a plain cell in one grid and
// the featured one in another. A span never exceeds the tracks the grid has
// at its current width (see `gridSpan`), so a bento collapses to a stack on a
// phone. The grid measures its tracks only while some cell spans.
//
// A flowing grid is an ordered collection: the order ops (ui-core
// `order.ts`) keep an order of keys and the cells draw by it.
//
// ## Placed
//
// `cols` (a track template, "2fr 1fr") makes it a board: a child at segment
// "r,c" sits at row r, column c (`grid[r, c]` in Python), and a place nobody
// fills stays empty. `rows` is the row template; rows past it size to their
// content. Spans keyed "r,c" cover tracks from that place, clipped at the
// board's last column. Keyed children ("note", "0") fill the free places,
// row after row, the way CSS auto placement does. Cells draw in reading
// order (placed ones by row then column, then the keyed ones), so a screen
// reader and a stacked board read the same. A board keeps no order: an
// order op is answered with an error and changes nothing.
//
// `stack_below` (px): under that width the board is one column, cells in
// that reading order and no spans, so a phone gets a stack.

import { asOrder, keyedOrder, ORDER_PROP, orderHandlers } from "@nustackdev/ui-core";
import { type CSSProperties, createContext, useContext, useMemo, useState } from "react";
import {
	type GridAlign,
	Grid as GridPrimitive,
	gridPlace,
	gridSpan,
	templateTracks,
	useTrackCount,
} from "../../components/ui/grid";
import { cn } from "../../lib/utils";
import {
	type CellProps,
	FlowProvider,
	indexedOrder,
	type NodeEntry,
	type NodeProps,
	NodeView,
	useBoolProp,
	useChildren,
	useNumberProp,
	useProp,
} from "../../tree";
import {
	type ChildMaps,
	childHandlers,
	type LayoutDefaults,
	readChildMaps,
	SELF,
	type Span,
	useChildMaps,
	useLayout,
	useWidth,
} from "./layout";

const DEFAULTS: LayoutDefaults = { gap: 4, padding: 0, justify: "stretch", align: "stretch" };
const ALIGNS: readonly GridAlign[] = ["stretch", "start", "center", "end"];
const asGridAlign = (v: string): GridAlign =>
	ALIGNS.includes(v as GridAlign) ? (v as GridAlign) : "stretch";

type Spans = Record<string, Span>;

/** A segment that names a place, "r,c", as [row, col]; anything else null. */
export function readPlace(segment: string): [number, number] | null {
	const m = /^(\d+),(\d+)$/.exec(segment);
	return m ? [Number(m[1]), Number(m[2])] : null;
}

/**
 * Children in reading order: placed ones ("r,c") by row then column, then
 * the keyed ones, positions in number order and names in write order.
 */
export function readingOrder(segments: readonly string[]): string[] {
	const placed: [string, number, number][] = [];
	const keyed: string[] = [];
	for (const s of segments) {
		const at = readPlace(s);
		if (at) placed.push([s, at[0], at[1]]);
		else keyed.push(s);
	}
	placed.sort((a, b) => a[1] - b[1] || a[2] - b[2]);
	return [...placed.map(([s]) => s), ...indexedOrder(keyed)];
}

type Mode = "flow" | "placed" | "stacked";

const CellContext = createContext<{ maps: ChildMaps; tracks: number; mode: Mode }>({
	maps: readChildMaps({}),
	tracks: Number.POSITIVE_INFINITY,
	mode: "flow",
});

/** Where a cell sits: a span in flow, a place (and span) on a board, nothing stacked. */
function cellStyle(
	segment: string,
	spans: Spans,
	tracks: number,
	mode: Mode,
): CSSProperties | undefined {
	if (mode === "stacked") return undefined;
	const span = spans[segment];
	if (mode === "placed") {
		const at = readPlace(segment);
		if (at) return gridPlace(at[0], at[1], span?.cols ?? 1, span?.rows ?? 1, tracks);
		// A keyed child on a board flows into a free place, spanning if asked.
		return span ? gridSpan(span.cols, span.rows, tracks) : undefined;
	}
	return span ? gridSpan(span.cols, span.rows, tracks) : undefined;
}

// One child, one cell. A one-track grid of its own, so the child fills the
// cell in both directions the way a direct grid item would, and min-width 0
// all the way down so a chart takes the cell's width, not its own.
function GridCell({ path, children }: CellProps) {
	const { maps, tracks, mode } = useContext(CellContext);
	const segment = String(path[path.length - 1]);
	const self = maps.alignSelf[segment];
	return (
		<div
			data-slot="grid-cell"
			data-cell={segment}
			className={cn("grid min-w-0 grid-cols-1", self && SELF[self])}
			style={cellStyle(segment, maps.span, tracks, mode)}
		>
			<FlowProvider flow="grid">{children}</FlowProvider>
		</div>
	);
}

const TRACK_FUNCTIONS = new Set(["repeat", "minmax", "fit-content", "min", "max", "calc"]);

/** A track template off the wire: text as is, a count as that many equal tracks. */
function readTemplate(raw: unknown): string {
	if (typeof raw === "number" && Number.isInteger(raw) && raw >= 1) {
		return `repeat(${raw}, minmax(0, 1fr))`;
	}
	if (typeof raw !== "string") return "";
	const text = raw.trim();
	// The same guard the Python side applies: track sizes and track functions only.
	if (!/^[a-z0-9.%(), -]+$/.test(text)) return "";
	for (const [, name] of text.matchAll(/([a-z-]+)\(/g)) {
		if (!TRACK_FUNCTIONS.has(name)) return "";
	}
	return text;
}

function GridView({ path }: NodeProps) {
	const layout = useLayout(path, DEFAULTS);
	const maxColumns = useNumberProp(path, "max_columns", 0);
	const minCellWidth = useNumberProp(path, "min_cell_width", 240);
	const dense = useBoolProp(path, "dense");
	const maps = useChildMaps(path);
	const cols = readTemplate(useProp<unknown>(path, "cols", ""));
	const rows = readTemplate(useProp<unknown>(path, "rows", ""));
	const stackBelow = useNumberProp(path, "stack_below", 0);
	const order = asOrder(useProp<unknown>(path, ORDER_PROP, undefined));
	const placed = cols !== "";
	const spanning = Object.keys(maps.span).length > 0;
	const [el, setEl] = useState<HTMLDivElement | null>(null);
	const flowTracks = useTrackCount(
		el,
		maxColumns,
		minCellWidth,
		maxColumns >= 1 ? Math.floor(maxColumns) : Number.POSITIVE_INFINITY,
		spanning && !placed,
	);
	const width = useWidth(el, placed && stackBelow > 0);
	const stacked = placed && width !== null && width < stackBelow;
	const mode: Mode = stacked ? "stacked" : placed ? "placed" : "flow";
	const tracks = placed ? templateTracks(cols) : flowTracks;

	const cellValue = useMemo(() => ({ maps, tracks, mode }), [maps, tracks, mode]);
	const written = useChildren(path);
	const drawn = useMemo(
		() => (placed ? readingOrder(written) : keyedOrder(order, written)),
		[placed, written, order],
	);

	return (
		<GridPrimitive
			ref={setEl}
			maxColumns={maxColumns}
			minCellWidth={minCellWidth}
			gap={layout.gap}
			align={asGridAlign(layout.align)}
			justify={asGridAlign(layout.justify)}
			padding={layout.padding}
			dense={dense}
			cols={stacked ? "minmax(0, 1fr)" : cols || undefined}
			rows={stacked ? undefined : rows || undefined}
			data-mode={mode}
			className={layout.scroll}
			style={layout.size}
		>
			<CellContext.Provider value={cellValue}>
				{drawn.map((segment) => (
					<GridCell key={segment} path={[...path, segment]}>
						<NodeView path={[...path, segment]} />
					</GridCell>
				))}
			</CellContext.Provider>
		</GridPrimitive>
	);
}

export const Grid: NodeEntry = {
	component: GridView,
	fill: true,
	handlers: {
		...orderHandlers((props) =>
			props.cols ? "a placed grid puts each cell at its place and keeps no order" : undefined,
		),
		...childHandlers,
	},
};
