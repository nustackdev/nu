// GaugeRef -- display-only circular dial showing a ratio in [0, 1].
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. Class-level defaults
// come in on the mount field `props` and seed the slice. Composes the kit
// Gauge primitive: variant maps to tone; the primitive owns arc geometry and
// value label; we add the optional caption below.

import { Gauge } from "../../components/ui/gauge";
import { Text } from "../../components/ui/text";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

type Variant = "neutral" | "ok" | "warn" | "danger";
type Tone = "accent" | "ok" | "warn" | "danger";

const VARIANTS = new Set<Variant>(["neutral", "ok", "warn", "danger"]);

const VARIANT_TO_TONE: Record<Variant, Tone> = {
	neutral: "accent",
	ok: "ok",
	warn: "warn",
	danger: "danger",
};

function clamp01(n: unknown): number {
	const v = Number(n);
	if (!Number.isFinite(v)) return 0;
	if (v < 0) return 0;
	if (v > 1) return 1;
	return v;
}

function normalizeVariant(v: unknown): Variant {
	if (typeof v !== "string") return "neutral";
	return VARIANTS.has(v as Variant) ? (v as Variant) : "neutral";
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
	const variant = useStore((s) => normalizeVariant(s.refs[path]?.variant));
	const tone = VARIANT_TO_TONE[variant];
	const pct = Math.round(value * 100);
	return (
		<div className="flex flex-col items-center gap-1">
			<Gauge
				value={pct}
				min={0}
				max={100}
				tone={tone}
				size="md"
				formatValue={(n) => `${n}%`}
				aria-label={caption || "gauge"}
			/>
			{caption && (
				<Text as="span" size="xs" tone="secondary">
					{caption}
				</Text>
			)}
		</div>
	);
}

export const GaugeRef: RefEntry = { factory, component: GaugeView };
