// PieChart -- display-only pie / donut chart.
//
// Server-owned. One `write` op carries every mutation (partial map);
// one `append` op pushes a single [label, value] slice. Class-level
// defaults (slices, colors, inner_radius, show_labels, show_legend,
// total_label) ride in on the mount field `props` and seed the slice.
// Composes the kit PieChart primitive; center label / total renders as an
// overlay on top of the primitive for donut mode.
//
// TODO(retune): the primitive does not yet expose a centerLabel slot, so
// we absolutely-position label + total over the chart. Follow-up: extend
// kit PieChart with a `centerLabel` prop.

import { Text } from "../../components/ui/text";
import { PieChart as KitPieChart } from "../../components/ui/pie-chart";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

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

const factory: SliceFactory = (path, ctx, props) => ({
	type: "PieChart",
	value: { slices: _toSlices(props?.slices) } as PieChartValue,
	colors: _colors(props?.colors),
	inner_radius: _radius(props?.inner_radius),
	show_labels: _bool(props?.show_labels, DEFAULTS.show_labels),
	show_legend: _bool(props?.show_legend, DEFAULTS.show_legend),
	total_label:
		typeof props?.total_label === "string" ? (props.total_label as string) : DEFAULTS.total_label,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as Record<string, unknown>;
			if ("slices" in p) slice.value = { slices: _toSlices(p.slices) };
			if ("colors" in p) slice.colors = _colors(p.colors);
			if ("inner_radius" in p) slice.inner_radius = _radius(p.inner_radius);
			if ("show_labels" in p) slice.show_labels = _bool(p.show_labels, DEFAULTS.show_labels);
			if ("show_legend" in p) slice.show_legend = _bool(p.show_legend, DEFAULTS.show_legend);
			if ("total_label" in p) {
				if (typeof p.total_label === "string") slice.total_label = p.total_label;
			}
		}),
	append: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			if (!Array.isArray(v) || v.length !== 2) return;
			const cur = slice.value as PieChartValue | undefined;
			const slices = Array.isArray(cur?.slices) ? [...cur.slices] : [];
			slices.push({ label: String(v[0]), value: _v(v[1]) });
			slice.value = { slices };
		}),
});

function PieChartView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as PieChartValue | undefined);
	const colors = useStore((s) => (s.refs[path]?.colors as string[]) ?? DEFAULTS.colors);
	const inner_radius = useStore((s) => (s.refs[path]?.inner_radius as number) ?? 0);
	const show_legend = useStore((s) => (s.refs[path]?.show_legend as boolean) ?? true);
	const total_label = useStore((s) => (s.refs[path]?.total_label as string) ?? "");
	const slices = Array.isArray(value?.slices) ? value.slices : [];
	const total = slices.reduce((a, s) => a + (Number.isFinite(s.value) ? s.value : 0), 0);
	const data = slices.map((s, i) => {
		const color = colors[i];
		return color
			? { name: s.label, value: s.value, color }
			: { name: s.label, value: s.value };
	});
	const innerRadius = inner_radius > 0 ? `${Math.round(inner_radius * 80)}%` : 0;
	const showCenter = inner_radius > 0 && total_label.length > 0;
	return (
		<div className="relative">
			<KitPieChart
				data={data}
				height={256}
				innerRadius={innerRadius}
				showLegend={show_legend}
			/>
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

export const PieChart: RefEntry = { factory, component: PieChartView };
