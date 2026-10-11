// Column -- vertical Section. Stacks its children with gap, alignment,
// justification, and padding.
//
// Children are not a prop and not a list of paths: they are the node's own
// children in the tree, in insertion order, which is the order they were
// first written in. `NodeChildren` renders them, so there is nothing to
// thread through and nothing to keep in sync.
//
// TODO(retune): the legacy Column Ref accepts numeric `gap` / `padding`
// (0..12+) and templates raw Tailwind class names. Under Tailwind v4 those
// arbitrary utilities need the JIT to see them at build time. We map the
// discrete step ladder (0/1/2/3/4/5/6/8/10/12) statically here so every
// possible class name is present in the compiled bundle. A proper `Stack`
// primitive with named tokens (`gap="md"`) is the follow-up; the wire
// contract stays numeric until then. A value off the ladder snaps to the
// nearest step.
//
// In the default stretch alignment each child sits in a `BlockCell`, the
// cell every block flow uses (see Row for the `fill` classification): a fill
// child stretches to the column's width, a content child keeps its own
// width at the start edge. Any other alignment applies to every child alike.

import {
	BareCell,
	BlockCell,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useNumberProp,
	useStringProp,
} from "../../tree";
import { stepClass } from "./row";

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
};

const JUSTIFY_CLASSES: Record<string, string> = {
	start: "justify-start",
	center: "justify-center",
	end: "justify-end",
	between: "justify-between",
	around: "justify-around",
};

function ColumnView({ path }: NodeProps) {
	const gap = useNumberProp(path, "gap", 4);
	const align = useStringProp(path, "align", "stretch");
	const justify = useStringProp(path, "justify", "start");
	const padding = useNumberProp(path, "padding", 0);

	const gapCls = stepClass(GAP_CLASSES, gap);
	const padCls = stepClass(PADDING_CLASSES, padding);
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.stretch;
	const justifyCls = JUSTIFY_CLASSES[justify] ?? JUSTIFY_CLASSES.start;

	return (
		<div className={`flex min-w-0 flex-col ${gapCls} ${padCls} ${alignCls} ${justifyCls}`}>
			<FlowProvider flow="block">
				<NodeChildren
					path={path}
					cell={alignCls === ALIGN_CLASSES.stretch ? BlockCell : BareCell}
				/>
			</FlowProvider>
		</div>
	);
}

export const Column: NodeEntry = { component: ColumnView, fill: true };
