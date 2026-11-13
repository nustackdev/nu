// InputGroup -- a field and the buttons that act on it, on one line.
//
// Built on the kit InputGroup (components/ui/input-group.tsx): the fill
// children (an input, a select, a date picker) take the width, the rest (a
// button, a toggle) keep their own, and every child sits on the line's
// bottom edge, so a labelled field's box lines up with its buttons. The app
// says nothing about grow or align: the group knows what it holds.
//
// Children draw in order, positions by number and names in the order first
// written, like a Row. Layout (`layout.tsx`): the size props, `scroll`, and
// `gap` (2) between the children. It is not an input itself: in a Form's
// values it nests its children by segment like any container.

import { InputGroup as InputGroupChrome } from "../../components/ui/input-group";
import { cn } from "../../lib/utils";
import {
	type CellProps,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useFill,
} from "../../tree";
import { gapClass, type LayoutDefaults, useLayout } from "./layout";

const DEFAULTS: LayoutDefaults = { gap: 2 };

function GroupCell({ path, children }: CellProps) {
	const fill = useFill(path);
	return (
		<div data-slot="input-group-cell" data-fill={fill ? "" : undefined} className="flex flex-col">
			{children}
		</div>
	);
}

function InputGroupView({ path }: NodeProps) {
	const layout = useLayout(path, DEFAULTS);
	return (
		<InputGroupChrome className={cn(gapClass(layout), layout.scroll)} style={layout.size}>
			<FlowProvider flow="row">
				<NodeChildren path={path} cell={GroupCell} indexed />
			</FlowProvider>
		</InputGroupChrome>
	);
}

export const InputGroup: NodeEntry = { component: InputGroupView, fill: true };
