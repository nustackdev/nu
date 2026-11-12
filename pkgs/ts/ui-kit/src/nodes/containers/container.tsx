// Container -- the page frame. A centred column capped at a page width.
//
// What a program puts its visible content in (see the `Container`
// primitive): full width to the cap, centred, fluid below it, a responsive
// side gutter, and its children stacked with `gap` between them. Layout
// (`layout.tsx`): `max_width` is the cap ("main" unless set; any length or
// page width name), `gap` (6), `padding` replaces the gutter with one step on
// every side, and the rest of a stack's layers and per child maps, through
// `StackChildren`.

import { Container as ContainerFrame } from "../../components/ui/container";
import { cn } from "../../lib/utils";
import type { NodeEntry, NodeProps } from "../../tree";
import {
	childHandlers,
	flowClass,
	flowStyle,
	type LayoutDefaults,
	StackChildren,
	useLayout,
} from "./layout";

const DEFAULTS: LayoutDefaults = { gap: 6, justify: "start", align: "stretch" };

function ContainerView({ path }: NodeProps) {
	const layout = useLayout(path, DEFAULTS);
	const capped = layout.size?.maxWidth !== undefined;
	return (
		<ContainerFrame
			maxWidth={capped ? "full" : "main"}
			padding={layout.padSet ? layout.padding : undefined}
			className={cn(flowClass(layout, "column", { padding: false }))}
			style={flowStyle(layout)}
		>
			<StackChildren path={path} layout={layout} />
		</ContainerFrame>
	);
}

export const Container: NodeEntry = {
	component: ContainerView,
	fill: true,
	handlers: childHandlers,
};
