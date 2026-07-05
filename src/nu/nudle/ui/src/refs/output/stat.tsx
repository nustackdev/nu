// StatRef -- display-only big number with label, optional delta and trend.
//
// Server-owned. One `write` op carries a partial map: missing keys leave the
// slice value untouched. Class-level defaults arrive on mount field `props`
// and seed the slice. Nu sentinels decode to "" for string fields and "flat"
// for trend.

import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const TREND_CLASSES: Record<string, string> = {
	up: "text-green-600",
	down: "text-red-600",
	flat: "text-gray-500",
};

const TREND_ARROW: Record<string, string> = {
	up: "↑",
	down: "↓",
	flat: "→",
};

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
	const trend = useStore((s) => (s.refs[path]?.trend as string) ?? "flat");
	const tcls = TREND_CLASSES[trend] ?? TREND_CLASSES.flat;
	const arrow = TREND_ARROW[trend] ?? TREND_ARROW.flat;
	return (
		<div className="flex flex-col gap-1">
			{label && <div className="text-xs uppercase text-gray-500">{label}</div>}
			<div className="text-3xl font-semibold tabular-nums">{value}</div>
			{delta && (
				<div className={`flex items-center gap-1 text-sm ${tcls}`}>
					<span aria-hidden>{arrow}</span>
					<span>{delta}</span>
				</div>
			)}
		</div>
	);
}

export const StatRef: RefEntry = { factory, component: StatView };
