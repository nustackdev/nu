// Collapsible -- one titled region whose children fold away. STUB: draws its
// children in a plain block so nothing is lost; the disclosure unit composes
// the Collapsible primitive, the open state and its notify.

import { FlowProvider, NodeChildren, type NodeEntry, type NodeProps } from "../../tree";

function CollapsibleView({ path }: NodeProps) {
	return (
		<div data-node="collapsible" className="flex flex-col gap-3">
			<FlowProvider flow="block">
				<NodeChildren path={path} />
			</FlowProvider>
		</div>
	);
}

export const Collapsible: NodeEntry = { component: CollapsibleView };
