// GaugeRef -- display-only circular dial showing a ratio in [0, 1].
//
// Server-owned. A write is a partial merge of {value, caption, variant} into
// the node's props, which is the default store behaviour, so there is no
// handler. The clamp and the variant whitelist moved from write time to read
// time -- same result, one less place to keep in sync. Composes the kit Gauge
// primitive: variant maps to tone; the primitive owns arc geometry and value
// label; we add the optional caption below.

import { Gauge } from "../../components/ui/gauge";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useNumberProp, useStringProp } from "../../tree";

type Variant = "neutral" | "ok" | "warn" | "danger";
type Tone = "accent" | "ok" | "warn" | "danger";

const VARIANTS = new Set<Variant>(["neutral", "ok", "warn", "danger"]);

const VARIANT_TO_TONE: Record<Variant, Tone> = {
	neutral: "accent",
	ok: "ok",
	warn: "warn",
	danger: "danger",
};

function clamp01(n: number): number {
	if (!Number.isFinite(n)) return 0;
	if (n < 0) return 0;
	if (n > 1) return 1;
	return n;
}

function normalizeVariant(v: string): Variant {
	return VARIANTS.has(v as Variant) ? (v as Variant) : "neutral";
}

function GaugeView({ path }: NodeProps) {
	const value = clamp01(useNumberProp(path, "value", 0));
	const caption = useStringProp(path, "caption");
	const variant = normalizeVariant(useStringProp(path, "variant", "neutral"));
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

export const GaugeRef: NodeEntry = { component: GaugeView };
