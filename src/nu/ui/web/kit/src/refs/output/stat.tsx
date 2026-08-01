// StatRef -- display-only big number with label, optional delta and trend.
//
// Server-owned. One `write` op carries a partial map: missing keys leave the
// slice value untouched. Class-level defaults arrive on mount field `props`
// and seed the slice. Nu sentinels decode to "" for string fields and "flat"
// for trend. Composes the kit Stat primitive family.

import { Stat, StatDelta, StatLabel, StatValue } from "../../components/ui/stat";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

type Trend = "up" | "down" | "flat";

function normTrend(v: unknown): Trend {
	if (v === "up" || v === "down" || v === "flat") return v;
	return "flat";
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "StatRef",
	value: typeof props?.value === "string" ? (props.value as string) : "",
	label: typeof props?.label === "string" ? (props.label as string) : "",
	delta: typeof props?.delta === "string" ? (props.delta as string) : "",
	trend: typeof props?.trend === "string" ? (props.trend as string) : "flat",
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				label?: unknown;
				value?: unknown;
				delta?: unknown;
				trend?: unknown;
			};
			if ("label" in p) {
				slice.label = p.label == null ? "" : String(p.label);
			}
			if ("value" in p) {
				slice.value = p.value == null ? "" : String(p.value);
			}
			if ("delta" in p) {
				slice.delta = p.delta == null ? "" : String(p.delta);
			}
			if ("trend" in p) {
				slice.trend = p.trend == null ? "flat" : String(p.trend);
			}
		}),
});

function StatView({ path }: { path: string }) {
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	const delta = useStore((s) => (s.refs[path]?.delta as string) ?? "");
	const trend = useStore((s) => normTrend(s.refs[path]?.trend));
	return (
		<Stat>
			{label && <StatLabel>{label}</StatLabel>}
			<StatValue>{value}</StatValue>
			{delta && <StatDelta direction={trend}>{delta}</StatDelta>}
		</Stat>
	);
}

export const StatRef: RefEntry = { factory, component: StatView };
