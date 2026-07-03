// GaugeRef -- display-only circular dial showing a ratio in [0, 1].
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. Class-level defaults
// come in on the mount field `props` and seed the slice.

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const VARIANTS = new Set(["neutral", "ok", "warn", "danger"]);

const COLORS: Record<string, string> = {
	neutral: "#3b82f6",
	ok: "#22c55e",
	warn: "#eab308",
	danger: "#ef4444",
};

function clamp01(n: unknown): number {
	const v = Number(n);
	if (!Number.isFinite(v)) return 0;
	if (v < 0) return 0;
	if (v > 1) return 1;
	return v;
}

function normalizeVariant(v: unknown): string {
	if (typeof v !== "string") return "neutral";
	return VARIANTS.has(v) ? v : "neutral";
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "GaugeRef",
	value: typeof props?.value === "number" ? clamp01(props.value) : 0,
	caption: typeof props?.caption === "string" ? (props.caption as string) : "",
	variant: normalizeVariant(props?.variant),
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				value?: unknown;
				caption?: unknown;
				variant?: unknown;
			};
			if ("value" in p) {
				slice.value = p.value == null ? 0 : clamp01(p.value);
			}
			if ("caption" in p) {
				slice.caption = p.caption == null ? "" : String(p.caption);
			}
			if ("variant" in p) {
				slice.variant = p.variant == null ? "neutral" : normalizeVariant(p.variant);
			}
		}),
});

function GaugeView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as number) ?? 0);
	const caption = useStore((s) => (s.refs[path]?.caption as string) ?? "");
	const variant = useStore((s) => (s.refs[path]?.variant as string) ?? "neutral");
	const pct = Math.round(value * 100);
	const r = 36;
	const c = 2 * Math.PI * r;
	const dash = `${value * c} ${c}`;
	const color = COLORS[variant] ?? COLORS.neutral;
	return (
		<div className="flex flex-col items-center">
			<div className="relative h-24 w-24">
				<svg viewBox="0 0 100 100" className="h-24 w-24 -rotate-90" role="img" aria-label="gauge">
					<circle cx="50" cy="50" r={r} fill="none" stroke="#e5e7eb" strokeWidth="8" />
					<circle
						cx="50"
						cy="50"
						r={r}
						fill="none"
						stroke={color}
						strokeWidth="8"
						strokeDasharray={dash}
						strokeLinecap="round"
					/>
				</svg>
				<div className="absolute inset-0 flex items-center justify-center text-sm tabular-nums">
					{pct}%
				</div>
			</div>
			{caption && <div className="mt-1 text-xs text-gray-600">{caption}</div>}
		</div>
	);
}

export const GaugeRef: RefEntry = { factory, component: GaugeView };
