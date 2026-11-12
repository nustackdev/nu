// Row -- horizontal Section. Arranges its children in a line with gap,
// alignment, justification, wrap, and padding.
//
// Children are the node's own children in the tree: positions (`row[0]`) in
// number order, names in the order they were first written.
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
// Fill: Chart (every chart type), DataTableRef, TreeRef,
// JsonViewerRef, LensRef, CodeRef, MarkdownRef, InputRef, NumberInputRef,
// TextAreaRef, TagInputRef, DatePickerRef, SliderRef, SketchRef, ProgressRef, AlertRef,
// EmptyStateRef, ImageRef, HeadingRef, PageLinkRef (but an inline one), and
// the containers Card, Box, Form, Fieldset, Field, Tabs, Accordion, Column,
// Row, ListRef, PageSection, NavList (Grid, Line, Select, Skeleton,
// Collapsible set their own). Content:
// everything else, including TextRef, LinkRef, BadgeRef, KbdRef, ShortcutRef,
// StatusDotRef, IconRef, NavItemRef,
// ButtonRef, CheckboxRef, SwitchRef, RadioGroupRef, StatRef, GaugeRef,
// DividerRef (drawn vertical here, it reads the row flow) and any type the
// registry does not know.
//
// A `grow` type (SpacerRef) is the one child that grows from nothing (flex
// 1 1 0): it takes whatever the line has left, so the children after it sit
// at the end. Two spacers split the rest between them.
//
// The row can still size one child against its kind, keyed by segment like
// a Grid's spans: `grow` {seg: weight} (a fill child weighs 1, so 2 takes
// twice its share; a content child given a weight grows too), `basis`
// {seg: px} the width a child starts from before growing (with no weight of
// its own it stays there, shrinking only once the line is full). `height`,
// `max_height` and `scroll` size the row itself (see `sizing.ts`).
//
// TODO(retune): same dynamic-class concern as Column -- numeric `gap` /
// `padding` template raw Tailwind class names, so we map the discrete step
// ladder statically to keep every candidate in the compiled bundle. A value
// off the ladder snaps to the nearest step rather than to a fixed fallback.

import { createContext, useContext } from "react";
import { GAP_CLASSES, PADDING_CLASSES, stepClass } from "../../lib/steps";
import { cn } from "../../lib/utils";
import {
	type CellProps,
	FlowProvider,
	isGrow,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useFill,
	useNode,
	useNumberProp,
	useStringProp,
} from "../../tree";
import { useSizing, useWeights, type Weights } from "./sizing";

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

type Sizing = { minWidth: number; stretch: boolean; grow: Weights; basis: Weights };

const SizingContext = createContext<Sizing>({
	minWidth: MIN_WIDTH,
	stretch: false,
	grow: {},
	basis: {},
});

/** The flex of one child: its kind's default, unless the row sizes it by segment. */
export function rowFlex(
	kind: "grow" | "fill" | "content",
	minWidth: number,
	weight: number | undefined,
	basis: number | undefined,
): string {
	const base = kind === "grow" ? "1 1 0px" : kind === "fill" ? `1 1 ${minWidth}px` : "0 1 auto";
	if (weight === undefined && basis === undefined) return base;
	const start =
		basis !== undefined
			? `${basis}px`
			: kind === "grow"
				? "0px"
				: kind === "fill"
					? `${minWidth}px`
					: "auto";
	return `${weight ?? 0} 1 ${start}`;
}

// One child, one cell. A flex column, so the child takes the cell's width.
// A fill cell always stretches to the line's height and its child grows to
// fill it, so cards side by side share one height and one top edge whatever
// the row's `align`; `align` places the content children (buttons, text,
// badges), which is what a toolbar wants centered. In a stretch row content
// children grow too.
function RowCell({ path, children }: CellProps) {
	const fill = useFill(path);
	const grow = isGrow(useNode(path).type);
	const { minWidth, stretch, grow: weights, basis } = useContext(SizingContext);
	const segment = String(path[path.length - 1]);
	const flex = rowFlex(
		grow ? "grow" : fill ? "fill" : "content",
		minWidth,
		weights[segment],
		basis[segment],
	);
	return (
		<div
			data-slot="row-cell"
			data-fill={fill ? "" : undefined}
			className={cn("flex flex-col", fill && "min-w-0 self-stretch *:grow", stretch && "*:grow")}
			style={{ flex }}
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
	const { grow, basis } = useWeights(path);
	const box = useSizing(path);

	const gapCls = stepClass(GAP_CLASSES, gap);
	const padCls = stepClass(PADDING_CLASSES, padding);
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.center;
	const justifyCls = JUSTIFY_CLASSES[justify] ?? JUSTIFY_CLASSES.start;
	const wrapCls = wrap ? "flex-wrap" : "flex-nowrap";

	return (
		<div
			className={cn(
				"flex min-w-0 flex-row",
				gapCls,
				padCls,
				alignCls,
				justifyCls,
				wrapCls,
				box.className,
			)}
			style={box.style}
		>
			<SizingContext.Provider value={{ minWidth, stretch: align === "stretch", grow, basis }}>
				<FlowProvider flow="row">
					<NodeChildren path={path} cell={RowCell} indexed />
				</FlowProvider>
			</SizingContext.Provider>
		</div>
	);
}

export const Row: NodeEntry = { component: RowView, fill: true };
