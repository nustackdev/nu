// NavList -- a run of nav items: a sidebar's list, or a top bar's links.
//
// Children are the node's own children in the tree, in insertion order.
// Mostly NavItemRefs, but any node goes: a Divider between groups, a Badge,
// a Button at the end of a bar. Drawn in a semantic <nav>, named by `label`.
//
// Chrome is plain props, merged by the default store `write`:
//
//   variant "vertical" (default) stacks the items, each a full width row,
//           under `label` as a small muted group heading when there is one.
//           Children get a block flow.
//           "horizontal" puts them on one line, each its own width, and the
//           line scrolls sideways (no scrollbar drawn) rather than wrap when
//           it runs out of room. Children get a row flow. `label` only
//           names the landmark there.
//
// The items read the flow to size themselves (see NavItemRef), so the same
// NavItem is a row in a sidebar and a tab-like link in a bar.

import { useId } from "react";
import { cn } from "../../lib/utils";
import {
	BareCell,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useStringProp,
} from "../../tree";

function NavListView({ path }: NodeProps) {
	const horizontal = useStringProp(path, "variant", "vertical") === "horizontal";
	const label = useStringProp(path, "label");
	const labelId = useId();
	// A drawn label names the landmark by reference; a bar has none to point
	// at, so it carries the name itself.
	const heading = !horizontal && label !== "";
	return (
		<nav
			data-slot="nav-list"
			data-variant={horizontal ? "horizontal" : "vertical"}
			aria-labelledby={heading ? labelId : undefined}
			aria-label={!heading && label !== "" ? label : undefined}
			className={cn(
				"flex min-w-0",
				horizontal
					? "scrollbar-none flex-row items-center gap-1 overflow-x-auto"
					: "flex-col gap-0.5",
			)}
		>
			{heading ? (
				<div id={labelId} className="px-3 pt-2 pb-1 font-medium text-text-muted text-xs">
					{label}
				</div>
			) : null}
			<FlowProvider flow={horizontal ? "row" : "block"}>
				<NodeChildren path={path} cell={BareCell} />
			</FlowProvider>
		</nav>
	);
}

export const NavList: NodeEntry = { component: NavListView, fill: true };
