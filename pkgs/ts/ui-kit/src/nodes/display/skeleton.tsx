// SkeletonRef -- pulsing placeholder lines while content loads. STUB: the
// smallest honest draw with the Skeleton primitive; the display unit owns
// shapes, height and the setters.

import { Skeleton } from "../../components/ui/skeleton";
import { type NodeEntry, type NodeProps, useNumberProp } from "../../tree";

function SkeletonView({ path }: NodeProps) {
	const lines = Math.max(1, Math.floor(useNumberProp(path, "lines", 1)));
	return (
		<div className="flex flex-col gap-2">
			{Array.from({ length: lines }, (_, i) => (
				<Skeleton key={i} shape="text" />
			))}
		</div>
	);
}

export const SkeletonRef: NodeEntry = { component: SkeletonView };
