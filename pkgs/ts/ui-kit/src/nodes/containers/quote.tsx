// Quote -- a header line over a body, set apart as quoted.
//
// One named child is the quote's own place: `header`, drawn on top across
// the full width, in a block flow so a Row or a Line there lays itself out
// and may truncate. The header box only places it. Without a header child
// the string `title` prop is the header line; with neither there is none.
// Every other child is the body, in write order.
//
// The look is the kit Quote primitive: an accent rule down the left edge
// and the primary ink rebound one step quieter inside. `title` comes in
// through a plain `write` the default merge handles, like a Collapsible's,
// so there is no handler here.
//
// The body is a stack (`layout.tsx`: `gap` 2, `padding`, `justify`,
// `align`, `divided`, the per child maps); the size props sit on the quote,
// and with `scroll` the body scrolls under the header. It has no intrinsic
// width, so it fills.

import { QuoteContent, QuoteHeader, Quote as QuotePrimitive } from "../../components/ui/quote";
import { cn } from "../../lib/utils";
import { type NodeEntry, type NodeProps, SlotView, useChildren, useStringProp } from "../../tree";
import {
	childHandlers,
	flowClass,
	flowStyle,
	type LayoutDefaults,
	StackChildren,
	useLayout,
} from "./layout";

const HEADER = "header";
const SLOTS: ReadonlySet<string> = new Set([HEADER]);
const DEFAULTS: LayoutDefaults = { gap: 2, justify: "start", align: "stretch" };

function QuoteView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const children = useChildren(path);
	const layout = useLayout(path, DEFAULTS);
	const hasHeader = children.includes(HEADER);
	const body = { ...layout, size: undefined };

	return (
		<QuotePrimitive data-node="quote" style={layout.size}>
			{hasHeader ? (
				<QuoteHeader>
					<SlotView path={path} segment={HEADER} />
				</QuoteHeader>
			) : title !== "" ? (
				<QuoteHeader>
					<span className="min-w-0 truncate">{title}</span>
				</QuoteHeader>
			) : null}
			<QuoteContent
				className={cn(flowClass(body, "column"), layout.scroll && "min-h-0 flex-1")}
				style={flowStyle(body)}
			>
				<StackChildren path={path} layout={body} skip={SLOTS} />
			</QuoteContent>
		</QuotePrimitive>
	);
}

export const Quote: NodeEntry = {
	component: QuoteView,
	fill: true,
	handlers: childHandlers,
};
