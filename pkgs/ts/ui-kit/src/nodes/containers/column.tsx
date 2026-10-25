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
//
// `max_width` caps the column at one of the kit's container widths
// (theme.css), and `center` (on by default) gives the capped column auto
// inline margins, which center it in a block or a flex column parent alike.
// "full", the default, caps nothing. A page is a Column with a max width.

import { GAP_CLASSES, PADDING_CLASSES, stepClass } from "../../lib/steps";
import { cn } from "../../lib/utils";
import {
	BareCell,
	BlockCell,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useNumberProp,
	useStringProp,
} from "../../tree";

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
	evenly: "justify-evenly",
};

// Container widths from theme.css, spelled out so Tailwind sees every class.
// Prose reads the theme token by name: `max-w-prose` is Tailwind's own 65ch
// utility, which wins over the theme's.
const MAX_WIDTH_CLASSES: Record<string, string> = {
	form: "max-w-form",
	prose: "max-w-(--container-prose)",
	panel: "max-w-panel",
	main: "max-w-main",
	wide: "max-w-dashboard",
};

function ColumnView({ path }: NodeProps) {
	const gap = useNumberProp(path, "gap", 4);
	const align = useStringProp(path, "align", "stretch");
	const justify = useStringProp(path, "justify", "start");
	const padding = useNumberProp(path, "padding", 0);
	const maxWidth = useStringProp(path, "max_width", "full");
	const center = useBoolProp(path, "center", true);

	const gapCls = stepClass(GAP_CLASSES, gap);
	const padCls = stepClass(PADDING_CLASSES, padding);
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.stretch;
	const justifyCls = JUSTIFY_CLASSES[justify] ?? JUSTIFY_CLASSES.start;
	const maxCls = MAX_WIDTH_CLASSES[maxWidth];

	return (
		<div
			data-max-width={maxCls ? maxWidth : undefined}
			className={cn(
				"flex min-w-0 flex-col",
				gapCls,
				padCls,
				alignCls,
				justifyCls,
				maxCls && ["w-full", maxCls],
				maxCls && center && "mx-auto",
			)}
		>
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
