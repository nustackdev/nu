// Grid -- children in equal cells, row after row.
//
// Children are the node's own children in the tree, in insertion order, one
// cell each. Composes the kit Grid primitive, which owns the track list:
// `columns` caps the cells on a row (0 lets the width decide), `min_width`
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
// ({columns, min_width, gap, align, padding, dense, spans}); `set_columns`
// from Python is a write of {columns}. `set_span` is its own op, {key, cols,
// rows}, merged into `spans` here, since a write would replace the whole map.
// Unknown values fall back to the defaults below.

import { createContext, useContext, useMemo, useState } from "react";
import {
	type GridAlign,
	Grid as GridPrimitive,
	gridSpan,
	useTrackCount,
} from "../../components/ui/grid";
import {
	type CellProps,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useEnumProp,
	useNumberProp,
	useProp,
} from "../../tree";

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

const SpanContext = createContext<{ spans: Spans; tracks: number }>({
	spans: NO_SPANS,
	tracks: Number.POSITIVE_INFINITY,
});

// One child, one cell. A one-track grid of its own, so the child fills the
// cell in both directions the way a direct grid item would, and min-width 0
// all the way down so a chart takes the cell's width, not its own.
function GridCell({ path, children }: CellProps) {
	const { spans, tracks } = useContext(SpanContext);
	const segment = String(path[path.length - 1]);
	const span = spans[segment];
	return (
		<div
			data-slot="grid-cell"
			data-cell={segment}
			className="grid min-w-0 grid-cols-1"
			style={span ? gridSpan(span.cols, span.rows, tracks) : undefined}
		>
			<FlowProvider flow="grid">{children}</FlowProvider>
		</div>
	);
}

function GridView({ path }: NodeProps) {
	const columns = useNumberProp(path, "columns", 0);
	const minWidth = useNumberProp(path, "min_width", 240);
	const gap = useNumberProp(path, "gap", 4);
	const align = useEnumProp(path, "align", ALIGNS, "stretch");
	const padding = useNumberProp(path, "padding", 0);
	const dense = useBoolProp(path, "dense");
	// The raw prop only changes identity when the spans do, so the cells
	// re-render on a span change and not on every grid render.
	const rawSpans = useProp<unknown>(path, "spans", null);
	const spans = useMemo(() => readSpans(rawSpans), [rawSpans]);
	const spanning = Object.keys(spans).length > 0;
	const [el, setEl] = useState<HTMLDivElement | null>(null);
	const tracks = useTrackCount(
		el,
		columns,
		minWidth,
		columns >= 1 ? Math.floor(columns) : Number.POSITIVE_INFINITY,
		spanning,
	);

	const spanValue = useMemo(() => ({ spans, tracks }), [spans, tracks]);

	return (
		<GridPrimitive
			ref={setEl}
			columns={columns}
			minWidth={minWidth}
			gap={gap}
			align={align}
			padding={padding}
			dense={dense}
		>
			<SpanContext.Provider value={spanValue}>
				<NodeChildren path={path} cell={GridCell} />
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
