// Grid -- children in equal cells, row after row.
//
// Children are the node's own children in the tree, in insertion order, one
// cell each. Composes the kit Grid primitive, which owns the track list:
// `max_columns` caps the cells on a row (0 lets the width decide), `min_width`
// is the narrowest a cell gets, so the same grid is three wide on a desktop
// and stacks on a phone.
//
// Each child sits in a cell box that hands it a "grid" flow and fills it:
// the child stretches to the cell's width, and to the row's height when
// `align` is "stretch", so a row of cards lines up whatever each one holds.
//
// The grid itself has no intrinsic width, so its entry declares `fill`: in a
// Row it takes a share of the free width instead of its content's size.
//
// Spans belong to the grid, not the cell: `spans` maps a child's segment to
// {cols, rows}, and that child's cell covers that many tracks. The child
// carries nothing, so the same Card is a plain cell in one grid and the
// featured one in another. A span never exceeds the tracks the grid has at
// its current width (see `gridSpan`), so a bento collapses to a stack on a
// phone. The grid measures its tracks only while some cell spans.
//
// Wire: chrome is plain props, merged by the default store `write`
// ({max_columns, min_width, gap, align, padding, dense, spans});
// `set_max_columns` from Python is a write of {max_columns}. `set_span` is
// its own op, {key, cols, rows}, merged into `spans` here, since a write
// would replace the whole map. A placed grid ships no `max_columns` or
// `min_width`, a flowing one no `cols` / `rows` / `stack_below`.
// Unknown values fall back to the defaults below.
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
// reader and a stacked board read the same.
//
// `stack_below` (px): under that width the board is one column, cells in
// that reading order and no spans, so a phone gets a stack. 0 never stacks.
//
// `height`, `max_height` and `scroll` size the grid (see `sizing.ts`); a
// board with `rows="auto 1fr"` and a height gives its last row the rest.

import {
	type CSSProperties,
	createContext,
	useContext,
	useLayoutEffect,
	useMemo,
	useState,
} from "react";
import {
	type GridAlign,
	Grid as GridPrimitive,
	gridPlace,
	gridSpan,
	templateTracks,
	useTrackCount,
} from "../../components/ui/grid";
import {
	type CellProps,
	FlowProvider,
	indexedOrder,
	type NodeEntry,
	type NodeProps,
	NodeView,
	useBoolProp,
	useChildren,
	useEnumProp,
	useNumberProp,
	useProp,
} from "../../tree";
import { useSizing } from "./sizing";

const ALIGNS: readonly GridAlign[] = ["stretch", "start", "center", "end"];

type Span = { cols: number; rows: number };
type Spans = Record<string, Span>;

const NO_SPANS: Spans = {};

/** `spans` off the wire: only entries with a whole span of 1 or more. */
export function readSpans(raw: unknown): Spans {
	if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return NO_SPANS;
	const out: Spans = {};
	for (const [key, v] of Object.entries(raw as Record<string, unknown>)) {
		if (v == null || typeof v !== "object") continue;
		const { cols, rows } = v as Record<string, unknown>;
		const c = Math.floor(Number(cols ?? 1));
		const r = Math.floor(Number(rows ?? 1));
		if (!(c >= 1) || !(r >= 1) || (c === 1 && r === 1)) continue;
		out[key] = { cols: c, rows: r };
	}
	return out;
}

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

const SpanContext = createContext<{ spans: Spans; tracks: number; mode: Mode }>({
	spans: NO_SPANS,
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
	const { spans, tracks, mode } = useContext(SpanContext);
	const segment = String(path[path.length - 1]);
	return (
		<div
			data-slot="grid-cell"
			data-cell={segment}
			className="grid min-w-0 grid-cols-1"
			style={cellStyle(segment, spans, tracks, mode)}
		>
			<FlowProvider flow="grid">{children}</FlowProvider>
		</div>
	);
}

/** The width of `el`, kept current as it resizes; null until measured or when off. */
function useWidth(el: HTMLElement | null, enabled: boolean): number | null {
	const [width, setWidth] = useState<number | null>(null);
	useLayoutEffect(() => {
		if (!el || !enabled || typeof ResizeObserver === "undefined") return;
		const measure = () => setWidth(el.clientWidth);
		measure();
		const observer = new ResizeObserver(measure);
		observer.observe(el);
		return () => observer.disconnect();
	}, [el, enabled]);
	return enabled ? width : null;
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
	const maxColumns = useNumberProp(path, "max_columns", 0);
	const minWidth = useNumberProp(path, "min_width", 240);
	const gap = useNumberProp(path, "gap", 4);
	const align = useEnumProp(path, "align", ALIGNS, "stretch");
	const padding = useNumberProp(path, "padding", 0);
	const dense = useBoolProp(path, "dense");
	// The raw prop only changes identity when the spans do, so the cells
	// re-render on a span change and not on every grid render.
	const rawSpans = useProp<unknown>(path, "spans", null);
	const spans = useMemo(() => readSpans(rawSpans), [rawSpans]);
	const cols = readTemplate(useProp<unknown>(path, "cols", ""));
	const rows = readTemplate(useProp<unknown>(path, "rows", ""));
	const stackBelow = useNumberProp(path, "stack_below", 0);
	const box = useSizing(path);
	const placed = cols !== "";
	const spanning = Object.keys(spans).length > 0;
	const [el, setEl] = useState<HTMLDivElement | null>(null);
	const flowTracks = useTrackCount(
		el,
		maxColumns,
		minWidth,
		maxColumns >= 1 ? Math.floor(maxColumns) : Number.POSITIVE_INFINITY,
		spanning && !placed,
	);
	const width = useWidth(el, placed && stackBelow > 0);
	const stacked = placed && width !== null && width < stackBelow;
	const mode: Mode = stacked ? "stacked" : placed ? "placed" : "flow";
	const tracks = placed ? templateTracks(cols) : flowTracks;

	const spanValue = useMemo(() => ({ spans, tracks, mode }), [spans, tracks, mode]);
	const written = useChildren(path);
	const order = useMemo(
		() => (placed ? readingOrder(written) : indexedOrder(written)),
		[placed, written],
	);

	return (
		<GridPrimitive
			ref={setEl}
			maxColumns={maxColumns}
			minWidth={minWidth}
			gap={gap}
			align={align}
			padding={padding}
			dense={dense}
			cols={stacked ? "minmax(0, 1fr)" : cols || undefined}
			rows={stacked ? undefined : rows || undefined}
			data-mode={mode}
			className={box.className}
			style={box.style}
		>
			<SpanContext.Provider value={spanValue}>
				{order.map((segment) => (
					<GridCell key={segment} path={[...path, segment]}>
						<NodeView path={[...path, segment]} />
					</GridCell>
				))}
			</SpanContext.Provider>
		</GridPrimitive>
	);
}

export const Grid: NodeEntry = {
	component: GridView,
	fill: true,
	handlers: {
		// One cell's span, merged into the map. cols and rows of 1 drop the
		// entry, so a cell goes back to plain.
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
