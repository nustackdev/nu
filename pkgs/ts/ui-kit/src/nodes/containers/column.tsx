// Column -- children stacked top to bottom.
//
// Children are its own, in the tree. Positions (`col[0]`)
// draw in number order, names in the order they were first written, until
// an order op arrives: from then on the column keeps an order of keys
// (`props.order`, see ui-core `order.ts`) and draws by it.
//
// Layout (`layout.tsx`): the size props, `padding` (0), `gap` (4), `justify`
// (start) down the column, `align` (stretch) across it, `divided`, and the
// per child maps (`grow`, `basis`, `align_self`, `sticky`) through
// `StackChildren`. In the stretch alignment a fill child stretches to the
// column's width and a content child keeps its own width at the start edge
// (`BlockCell`); any other alignment applies to every child alike.
//
// `max_width` takes the whole width up to it. Where a capped column sits is
// its parent's to say (`align`, or `align_self` for it alone).

import { asOrder, ORDER_PROP, orderHandlers } from "@nustackdev/ui-core";
import { cn } from "../../lib/utils";
import { type NodeEntry, type NodeProps, useProp } from "../../tree";
import {
	childHandlers,
	flowClass,
	flowStyle,
	type LayoutDefaults,
	StackChildren,
	useLayout,
} from "./layout";

const DEFAULTS: LayoutDefaults = { gap: 4, padding: 0, justify: "start", align: "stretch" };

function ColumnView({ path }: NodeProps) {
	const layout = useLayout(path, DEFAULTS);
	const order = asOrder(useProp<unknown>(path, ORDER_PROP, undefined));
	const capped = layout.size?.maxWidth !== undefined;
	return (
		<div
			className={cn("flex min-w-0 flex-col", flowClass(layout, "column"), capped && "w-full")}
			style={flowStyle(layout)}
		>
			<StackChildren path={path} layout={layout} order={order} />
		</div>
	);
}

export const Column: NodeEntry = {
	component: ColumnView,
	fill: true,
	handlers: { ...orderHandlers(), ...childHandlers },
};
