// Sheet -- edge drawer over the page, children as its body. STUB: draws its
// children in a plain block so nothing is lost; the disclosure unit composes
// the Sheet primitive, `open` / `side` and the dismiss notify.

import { FlowProvider, NodeChildren, type NodeEntry, type NodeProps } from "../../tree";

function SheetView({ path }: NodeProps) {
	return (
		<div data-node="sheet" className="flex flex-col gap-4">
			<FlowProvider flow="block">
				<NodeChildren path={path} />
			</FlowProvider>
		</div>
	);
}

export const Sheet: NodeEntry = { component: SheetView };
