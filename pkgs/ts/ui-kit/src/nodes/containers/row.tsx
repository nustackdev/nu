// Row -- horizontal Section. Arranges its children in a line with gap,
// alignment, justification, wrap, and padding.
//
// Children are the node's own children in the tree, in insertion order.
// `NodeChildren` does the lookup, the recursion and the error boundary, so
// there is no child path list to thread through and nothing to keep in sync.
//
// Chrome is plain props: the default store `write` merges an object payload
// into them, and the read-time coercions below apply the same defaults the
// old factory applied, so there is no handler here.
//
// Sizing comes from the child's kind, never from a prop on the child. Each
// child sits in a cell, and the cell reads the child's `fill` hint:
//
//   fill     no width of its own. The cell grows from a basis of the row's
//            `min_width` (px) and may shrink below it: fill children share
//            the free width equally, never collapse to nothing, and in a
//            wrapping row wrap at `min_width`, several per line.
//   content  sizes to itself (flex 0 1 auto). It may shrink down to its
//            longest word, so long text wraps instead of pushing the row
//            wider; a button or badge never shrinks below its label.
//
// Fill: LineChart, AreaChart, BarChart, PieChart, TableRef, TreeRef,
// JsonViewerRef, LensRef, CodeRef, MarkdownRef, InputRef, NumberInputRef,
// TextAreaRef, TagInputRef, DatePickerRef, SliderRef, ProgressRef, AlertRef,
// EmptyStateRef, ImageRef, HeadingRef, and the containers Card, Container,
// Form, Fieldset, Field, Tabs, Accordion, Column, Row, ListRef (Grid, Line,
// Select, Skeleton, Collapsible set their own). Content: everything else,
// including TextRef, LinkRef, BadgeRef, KbdRef, ShortcutRef, StatusDotRef,
// ButtonRef, CheckboxRef, SwitchRef, RadioGroupRef, StatRef, GaugeRef,
// DividerRef (drawn vertical here, it reads the row flow) and any type the
// registry does not know.
//
// TODO(retune): same dynamic-class concern as Column -- numeric `gap` /
// `padding` template raw Tailwind class names, so we map the discrete step
// ladder statically to keep every candidate in the compiled bundle. A value
// off the ladder snaps to the nearest step rather than to a fixed fallback.

import { createContext, useContext } from "react";
import { cn } from "../../lib/utils";
import {
	type CellProps,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useFill,
	useNumberProp,
	useStringProp,
} from "../../tree";

const GAP_CLASSES: Record<number, string> = {
	0: "gap-0",
	1: "gap-1",
	2: "gap-2",
	3: "gap-3",
	4: "gap-4",
	5: "gap-5",
	6: "gap-6",
	8: "gap-8",
	10: "gap-10",
	12: "gap-12",
	16: "gap-16",
};

const PADDING_CLASSES: Record<number, string> = {
	0: "p-0",
	1: "p-1",
	2: "p-2",
	3: "p-3",
	4: "p-4",
	5: "p-5",
	6: "p-6",
	8: "p-8",
	10: "p-10",
	12: "p-12",
	16: "p-16",
};

const ALIGN_CLASSES: Record<string, string> = {
	start: "items-start",
	center: "items-center",
	end: "items-end",
	stretch: "items-stretch",
	baseline: "items-baseline",
};

const JUSTIFY_CLASSES: Record<string, string> = {
	start: "justify-start",
	center: "justify-center",
	end: "justify-end",
	between: "justify-between",
	around: "justify-around",
	evenly: "justify-evenly",
};

const MIN_WIDTH = 240;

/** The class for the ladder step nearest `n` (ties go to the smaller step). */
export function stepClass(ladder: Record<number, string>, n: number): string {
	let best = 0;
	for (const key of Object.keys(ladder).map(Number)) {
		if (Math.abs(key - n) < Math.abs(best - n)) best = key;
	}
	return ladder[best];
}

type Sizing = { minWidth: number; stretch: boolean };

const SizingContext = createContext<Sizing>({ minWidth: MIN_WIDTH, stretch: false });

// One child, one cell. A flex column, so the child takes the cell's width; in
// a stretch row the child also grows to the cell's height.
function RowCell({ path, children }: CellProps) {
	const fill = useFill(path);
	const { minWidth, stretch } = useContext(SizingContext);
	return (
		<div
			data-slot="row-cell"
			data-fill={fill ? "" : undefined}
			className={cn("flex flex-col", fill && "min-w-0", stretch && "*:grow")}
			style={{ flex: fill ? `1 1 ${minWidth}px` : "0 1 auto" }}
		>
			{children}
		</div>
	);
}

function RowView({ path }: NodeProps) {
	const gap = useNumberProp(path, "gap", 4);
	const align = useStringProp(path, "align", "center");
	const justify = useStringProp(path, "justify", "start");
	const wrap = useBoolProp(path, "wrap");
	const padding = useNumberProp(path, "padding", 0);
	const minWidth = Math.max(0, useNumberProp(path, "min_width", MIN_WIDTH));

	const gapCls = stepClass(GAP_CLASSES, gap);
	const padCls = stepClass(PADDING_CLASSES, padding);
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.center;
	const justifyCls = JUSTIFY_CLASSES[justify] ?? JUSTIFY_CLASSES.start;
	const wrapCls = wrap ? "flex-wrap" : "flex-nowrap";

	return (
		<div
			className={`flex min-w-0 flex-row ${gapCls} ${padCls} ${alignCls} ${justifyCls} ${wrapCls}`}
		>
			<SizingContext.Provider value={{ minWidth, stretch: align === "stretch" }}>
				<FlowProvider flow="row">
					<NodeChildren path={path} cell={RowCell} />
				</FlowProvider>
			</SizingContext.Provider>
		</div>
	);
}

export const Row: NodeEntry = { component: RowView, fill: true };
