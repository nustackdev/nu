// Line -- children inline, wrapping like a paragraph. STUB: registered and
// drawing its children in the Line primitive stub; the line unit owns the
// inline rhythm and how each content leaf draws inline.
//
// Children see an "inline" flow.

import { Line as LinePrimitive } from "../../components/ui/line";
import { FlowProvider, NodeChildren, type NodeEntry, type NodeProps } from "../../tree";

function LineView({ path }: NodeProps) {
	return (
		<LinePrimitive>
			<FlowProvider flow="inline">
				<NodeChildren path={path} />
			</FlowProvider>
		</LinePrimitive>
	);
}

export const Line: NodeEntry = { component: LineView };
