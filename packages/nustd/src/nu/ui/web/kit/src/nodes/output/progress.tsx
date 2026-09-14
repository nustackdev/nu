// ProgressRef -- display-only progress bar in [0, 1] with optional caption.
//
// Server-owned. A write is a partial merge of {value, caption, indeterminate}
// into the node's props, which is the default store behaviour, so there is no
// handler. The clamp moved from write time to read time. Composes the kit
// Progress primitive; indeterminate is signaled to Radix by passing null.

import { Progress } from "../../components/ui/progress";
import { Text } from "../../components/ui/text";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useNumberProp,
	useStringProp,
} from "../../tree";

function clamp01(n: number): number {
	if (!Number.isFinite(n)) return 0;
	if (n < 0) return 0;
	if (n > 1) return 1;
	return n;
}

function ProgressView({ path }: NodeProps) {
	const value = clamp01(useNumberProp(path, "value", 0));
	const caption = useStringProp(path, "caption");
	const indeterminate = useBoolProp(path, "indeterminate");
	const pct = Math.round(value * 100);
	return (
		<div className="flex w-full flex-col gap-1">
			<Progress value={indeterminate ? null : pct} max={100} />
			{caption && (
				<Text as="span" size="xs" tone="secondary">
					{caption}
				</Text>
			)}
		</div>
	);
}

export const ProgressRef: NodeEntry = { component: ProgressView };
