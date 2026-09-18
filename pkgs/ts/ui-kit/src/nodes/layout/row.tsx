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
// TODO(retune): same dynamic-class concern as Column -- numeric `gap` /
// `padding` template raw Tailwind class names, so we map the discrete step
// ladder statically to keep every candidate in the compiled bundle.

import {
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useBoolProp,
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

function RowView({ path }: NodeProps) {
	const gap = useNumberProp(path, "gap", 4);
	const align = useStringProp(path, "align", "center");
	const justify = useStringProp(path, "justify", "start");
	const wrap = useBoolProp(path, "wrap");
	const padding = useNumberProp(path, "padding", 0);

	const gapCls = GAP_CLASSES[gap] ?? GAP_CLASSES[4];
	const padCls = PADDING_CLASSES[padding] ?? PADDING_CLASSES[0];
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.center;
	const justifyCls = JUSTIFY_CLASSES[justify] ?? JUSTIFY_CLASSES.start;
	const wrapCls = wrap ? "flex-wrap" : "flex-nowrap";

	return (
		<div className={`flex flex-row ${gapCls} ${padCls} ${alignCls} ${justifyCls} ${wrapCls}`}>
			<NodeChildren path={path} />
		</div>
	);
}

export const Row: NodeEntry = { component: RowView };
