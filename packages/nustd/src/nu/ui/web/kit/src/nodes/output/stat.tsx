// StatRef -- display-only big number with label, optional delta and trend.
//
// Server-owned. A write is a partial merge of {label, value, delta, trend}
// into the node's props, which is the default store behaviour, so there is no
// handler. Nu sentinels read back as "" for the string slots and "flat" for
// trend at render time. Composes the kit Stat primitive family.

import { Stat, StatDelta, StatLabel, StatValue } from "../../components/ui/stat";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

type Trend = "up" | "down" | "flat";

function normTrend(v: string): Trend {
	if (v === "up" || v === "down" || v === "flat") return v;
	return "flat";
}

function StatView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const value = useStringProp(path, "value");
	const delta = useStringProp(path, "delta");
	const trend = normTrend(useStringProp(path, "trend", "flat"));
	return (
		<Stat>
			{label && <StatLabel>{label}</StatLabel>}
			<StatValue>{value}</StatValue>
			{delta && <StatDelta direction={trend}>{delta}</StatDelta>}
		</Stat>
	);
}

export const StatRef: NodeEntry = { component: StatView };
