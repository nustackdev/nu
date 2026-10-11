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
// Wire: chrome is plain props, merged by the default store `write`
// ({columns, min_width, gap, align, padding}); `set_columns` from Python is
// a write of {columns}. Unknown values fall back to the defaults below.

import { type GridAlign, Grid as GridPrimitive } from "../../components/ui/grid";
import {
	type CellProps,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useNumberProp,
	useStringProp,
} from "../../tree";

const ALIGNS = new Set<GridAlign>(["stretch", "start", "center", "end"]);

// One child, one cell. A one-track grid of its own, so the child fills the
// cell in both directions the way a direct grid item would, and min-width 0
// all the way down so a chart takes the cell's width, not its own.
function GridCell({ path, children }: CellProps) {
	return (
		<div
			data-slot="grid-cell"
			data-cell={path[path.length - 1]}
			className="grid min-w-0 grid-cols-1"
		>
			<FlowProvider flow="grid">{children}</FlowProvider>
		</div>
	);
}

function GridView({ path }: NodeProps) {
	const columns = useNumberProp(path, "columns", 0);
	const minWidth = useNumberProp(path, "min_width", 240);
	const gap = useNumberProp(path, "gap", 4);
	const align = useStringProp(path, "align", "stretch") as GridAlign;
	const padding = useNumberProp(path, "padding", 0);

	return (
		<GridPrimitive
			columns={columns}
			minWidth={minWidth}
			gap={gap}
			align={ALIGNS.has(align) ? align : "stretch"}
			padding={padding}
		>
			<NodeChildren path={path} cell={GridCell} />
		</GridPrimitive>
	);
}

export const Grid: NodeEntry = { component: GridView, fill: true };
