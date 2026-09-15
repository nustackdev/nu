// The one node type nudle itself owns.
//
// A Page is a plain column of whatever was declared on it. Its `route` and
// `label` props are for the router and the sidebar; the page does not read
// them. Registered here rather than in the kit because a page at the top of
// the tree is nudle's shape, not every host's.

import { NodeChildren, type NodeProps, register } from "@nustackdev/ui-kit";

function PageView({ path }: NodeProps) {
	return (
		<div className="flex flex-col gap-6">
			<NodeChildren path={path} />
		</div>
	);
}

register("Page", { component: PageView });
