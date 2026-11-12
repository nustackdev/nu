// Row -- children side by side, left to right.
//
// Children are its own, in the tree: positions (`row[0]`) in
// number order, names in the order they were first written, until an order
// op arrives (see ui-core `order.ts`); from then on the row keeps an order
// of keys and draws by it.
//
// Layout (`layout.tsx`): the size props, `padding` (0), `gap` (4), `justify`
// (start) along the row, `align` (center) across it, baseline included,
// `divided`. `wrap` lets children run onto more lines. `stack_below` (px):
// narrower than that, the row is a column, every child its full width.
//
// Sizing comes from the child's kind, never from a prop on the child. Each
// child sits in a cell, and the cell reads the child's `fill` hint:
//
//   fill     no width of its own. The cell grows from a basis of 240px and
//            may shrink below it: fill children share the free width
//            equally, never collapse to nothing, and in a wrapping row wrap
//            at 240px, several per line.
//   content  sizes to itself (flex 0 1 auto). It may shrink down to its
//            longest word, so long text wraps instead of pushing the row
//            wider; a button or badge never shrinks below its label.
//
// Fill: Chart (every chart type), DataTableRef, TreeRef,
// JsonViewerRef, LensRef, CodeRef, MarkdownRef, InputRef, NumberInputRef,
// TextAreaRef, TagInputRef, DatePickerRef, SliderRef, SketchRef, ProgressRef, AlertRef,
// EmptyStateRef, ImageRef, HeadingRef, PageLinkRef (but an inline one), and
// the containers Card, Form, Fieldset, Field, Tabs, Accordion, Column,
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
// A `grow` type (SpacerRef) is the one child that grows from nothing (flex
// 1 1 0): it takes whatever the line has left, so the children after it sit
// at the end. Two spacers split the rest between them.
//
// The row sizes one child against its kind through its per child maps,
// keyed by segment: `grow` is a true ratio of the free width (a grown child
// starts from 0, so 1 and 2 draw 1:2; in a wrapping row a grown fill child
// keeps 240px as its narrowest, so it still wraps), `basis` the width a
// child starts from, `align_self`, and `sticky` ("left" / "right").

import { asOrder, ORDER_PROP, orderHandlers } from "@nustackdev/ui-core";
import { type CSSProperties, createContext, useContext, useMemo, useState } from "react";
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
	useProp,
} from "../../tree";
import {
	type ChildMaps,
	childHandlers,
	flowClass,
	flowStyle,
	type LayoutDefaults,
	readChildMaps,
	SELF,
	stickyStyle,
	useChildMaps,
	useLayout,
	useWidth,
} from "./layout";

/** The basis a fill child grows from, and the narrowest it wraps at. */
export const FILL_BASIS = 240;

const DEFAULTS: LayoutDefaults = { gap: 4, padding: 0, justify: "start", align: "center" };

type RowContextValue = { maps: ChildMaps; stretch: boolean; wrap: boolean; stacked: boolean };

const RowContext = createContext<RowContextValue>({
	maps: readChildMaps({}),
	stretch: false,
	wrap: false,
	stacked: false,
});

/** The flex of one child: its kind's default, unless the row sizes it by segment. */
export function rowFlex(
	kind: "grow" | "fill" | "content",
	weight: number | undefined,
	basis: string | undefined,
): string {
	if (weight === undefined && basis === undefined) {
		return kind === "grow" ? "1 1 0px" : kind === "fill" ? `1 1 ${FILL_BASIS}px` : "0 1 auto";
	}
	return `${weight ?? 0} 1 ${basis ?? (weight !== undefined ? "0px" : "auto")}`;
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
	const { maps, stretch, wrap, stacked } = useContext(RowContext);
	const segment = String(path[path.length - 1]);
	const weight = maps.grow[segment];
	const self = maps.alignSelf[segment];
	const style: CSSProperties = {
		flex: stacked
			? "0 0 auto"
			: rowFlex(grow ? "grow" : fill ? "fill" : "content", weight, maps.basis[segment]),
		...stickyStyle(maps.sticky[segment]),
	};
	if (wrap && fill && weight !== undefined && !stacked) style.minWidth = `${FILL_BASIS}px`;
	return (
		<div
			data-slot="row-cell"
			data-fill={fill ? "" : undefined}
			className={cn(
				"flex flex-col",
				fill && "min-w-0 self-stretch *:grow",
				stretch && "*:grow",
				self && SELF[self],
			)}
			style={style}
		>
			{children}
		</div>
	);
}

function RowView({ path }: NodeProps) {
	const layout = useLayout(path, DEFAULTS);
	const wrap = useBoolProp(path, "wrap");
	const stackBelow = useNumberProp(path, "stack_below", 0);
	const order = asOrder(useProp<unknown>(path, ORDER_PROP, undefined));
	const maps = useChildMaps(path);
	const [el, setEl] = useState<HTMLDivElement | null>(null);
	const width = useWidth(el, stackBelow > 0);
	const stacked = width !== null && width < stackBelow;
	const value = useMemo(
		() => ({ maps, stretch: layout.align === "stretch", wrap, stacked }),
		[maps, layout.align, wrap, stacked],
	);

	return (
		<div
			ref={setEl}
			data-stacked={stacked ? "" : undefined}
			className={cn(
				"flex min-w-0",
				stacked ? "flex-col" : "flex-row",
				flowClass(stacked ? { ...layout, align: "stretch" } : layout, stacked ? "column" : "row"),
				wrap && !stacked ? "flex-wrap" : "flex-nowrap",
			)}
			style={flowStyle(layout)}
		>
			<RowContext.Provider value={value}>
				<FlowProvider flow="row">
					<NodeChildren path={path} cell={RowCell} indexed order={order} />
				</FlowProvider>
			</RowContext.Provider>
		</div>
	);
}

export const Row: NodeEntry = {
	component: RowView,
	fill: true,
	handlers: { ...orderHandlers(), ...childHandlers },
};
