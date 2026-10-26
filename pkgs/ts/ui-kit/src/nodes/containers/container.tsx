// Container -- the page frame. A centred column capped at a page width.
//
// What a program puts its visible content in (see the `Container`
// primitive): full width to the cap, centred, fluid below it, a responsive
// side gutter, and its children stacked with `gap` between them. `size` is a
// page width name, `gap` a step on the spacing ladder, `padding` "none" for
// edge to edge. Children are the node's own, in insertion order, each in the
// `BlockCell` a block flow uses, as in a Column.

import {
	type ContainerPadding,
	Container as ContainerFrame,
	PAGE_WIDTH_CLASSES,
	type PageWidth,
} from "../../components/ui/container";
import { GAP_CLASSES, stepClass } from "../../lib/steps";
import {
	BlockCell,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useNumberProp,
	useStringProp,
} from "../../tree";

function ContainerView({ path }: NodeProps) {
	const raw = useStringProp(path, "size", "main");
	const size: PageWidth = raw in PAGE_WIDTH_CLASSES ? (raw as PageWidth) : "main";
	const gap = useNumberProp(path, "gap", 6);
	const pad = useStringProp(path, "padding", "gutter");
	const padding: ContainerPadding = pad === "none" ? "none" : "gutter";
	return (
		<ContainerFrame size={size} padding={padding} className={stepClass(GAP_CLASSES, gap)}>
			<FlowProvider flow="block">
				<NodeChildren path={path} cell={BlockCell} />
			</FlowProvider>
		</ContainerFrame>
	);
}

export const Container: NodeEntry = { component: ContainerView, fill: true };
