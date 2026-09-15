// PieChart -- display-only pie / donut chart.
//
// Server-owned. Chrome (colors, inner_radius, show_labels, show_legend,
// total_label) is plain props, declared at the slot and coerced where it is
// read. The slices live on `value` as {slices: [{label, value}, ...]}.
//
// Two handlers. `write` carries a partial map whose `slices` needs shape
// coercion (pairs or bare values on the same key) before it can be drawn,
// which the default merge does not do. `append` pushes one slice, which is
// not a write at all. Composes the kit PieChart primitive; center label /
// total renders as an overlay on top of the primitive for donut mode.
//
// The slot may declare `slices` up front. That is a prop like any other now,
// so instead of the old factory seeding `value` from it at mount, `value`
// falls back to it until the first write that names slices.
//
// TODO(retune): the primitive does not yet expose a centerLabel slot, so
// we absolutely-position label + total over the chart. Follow-up: extend
// kit PieChart with a `centerLabel` prop.

import type { Props } from "@nustackdev/ui-core";
import { PieChart as KitPieChart } from "../../components/ui/pie-chart";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useProp, useProps, useStringProp } from "../../tree";

type Slice = { label: string; value: number };
type PieChartValue = { slices: Slice[] };

const DEFAULTS = {
	colors: [] as string[],
	inner_radius: 0,
	show_labels: true,
	show_legend: true,
	total_label: "",
};

function _v(v: unknown): number {
	const n = typeof v === "number" ? v : Number(v);
	if (!Number.isFinite(n) || n < 0) return 0;
	return n;
}

function _radius(v: unknown): number {
	const n = typeof v === "number" ? v : Number(v);
	if (!Number.isFinite(n)) return 0;
	if (n < 0) return 0;
	if (n > 0.95) return 0.95;
	return n;
}

function _bool(v: unknown, fallback: boolean): boolean {
	return typeof v === "boolean" ? v : fallback;
}

function _colors(v: unknown): string[] {
	if (!Array.isArray(v)) return [];
	return v.filter((c): c is string => typeof c === "string");
}

// A write payload that is not a map carries nothing this type understands.
function _map(v: unknown): Record<string, unknown> {
	return v != null && typeof v === "object" && !Array.isArray(v)
		? (v as Record<string, unknown>)
		: {};
}

function _toSlices(v: unknown): Slice[] {
	if (v && typeof v === "object" && !Array.isArray(v) && "slices" in v) {
		return _toSlices((v as { slices: unknown }).slices);
	}
	if (!Array.isArray(v)) return [];
	if (v.length === 0) return [];
	const pairs = v.every((e) => Array.isArray(e) && (e as unknown[]).length === 2);
	if (pairs) {
		return (v as unknown[][]).map((p) => ({
			label: String(p[0]),
			value: _v(p[1]),
		}));
	}
	return v.map((val, i) => ({ label: String(i), value: _v(val) }));
}

// `value` once anything has written it, the slot's declared `slices` before.
function _slices(props: Props): Slice[] {
	const cur = props.value as PieChartValue | undefined | null;
	if (Array.isArray(cur?.slices)) return cur.slices as Slice[];
	return _toSlices(props.slices);
}

function PieChartView({ path }: NodeProps) {
	const slices = _slices(useProps(path));
	const colors = _colors(useProp<unknown>(path, "colors", undefined));
	const inner_radius = _radius(useProp<unknown>(path, "inner_radius", undefined));
	const show_legend = _bool(useProp<unknown>(path, "show_legend", undefined), DEFAULTS.show_legend);
	const total_label = useStringProp(path, "total_label", DEFAULTS.total_label);
	const total = slices.reduce((a, s) => a + (Number.isFinite(s.value) ? s.value : 0), 0);
	const data = slices.map((s, i) => {
		const color = colors[i];
		return color ? { name: s.label, value: s.value, color } : { name: s.label, value: s.value };
	});
	const innerRadius = inner_radius > 0 ? `${Math.round(inner_radius * 80)}%` : 0;
	const showCenter = inner_radius > 0 && total_label.length > 0;
	return (
		<div className="relative">
			<KitPieChart data={data} height={256} innerRadius={innerRadius} showLegend={show_legend} />
			{showCenter && (
				<div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
					<Text as="span" size="sm" tone="secondary">
						{total_label}
					</Text>
					<Text as="span" size="lg" tone="primary" weight="semibold">
						{total}
					</Text>
				</div>
			)}
		</div>
	);
}

export const PieChart: NodeEntry = {
	component: PieChartView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				const p = _map(payload);
				if ("slices" in p) props.value = { slices: _toSlices(p.slices) };
				if ("colors" in p) props.colors = _colors(p.colors);
				if ("inner_radius" in p) props.inner_radius = _radius(p.inner_radius);
				if ("show_labels" in p) props.show_labels = _bool(p.show_labels, DEFAULTS.show_labels);
				if ("show_legend" in p) props.show_legend = _bool(p.show_legend, DEFAULTS.show_legend);
				if ("total_label" in p) {
					if (typeof p.total_label === "string") props.total_label = p.total_label;
				}
			}),
		append: (ctx, payload) =>
			ctx.update((props) => {
				if (!Array.isArray(payload) || payload.length !== 2) return;
				const slices = [..._slices(props)];
				slices.push({ label: String(payload[0]), value: _v(payload[1]) });
				props.value = { slices };
			}),
	},
};
