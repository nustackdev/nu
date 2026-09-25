// EmptyStateRef -- what a region says while it has nothing to show.
//
// Server-owned. A write is a partial merge of `label` / `description` /
// `size` into the node's props, which is the default store behaviour, so this
// type is a component and nothing else. Composes the kit EmptyState primitive.

import { EmptyState } from "../../components/ui/empty-state";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

function EmptyStateView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const description = useStringProp(path, "description");
	const size = useStringProp(path, "size", "md") === "sm" ? "sm" : "md";
	return (
		<EmptyState size={size} description={description || undefined}>
			{label}
		</EmptyState>
	);
}

export const EmptyStateRef: NodeEntry = { component: EmptyStateView };
