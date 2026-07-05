// PieChart -- display-only pie / donut chart, recharts.
//
// Server-owned. One `write` op carries every mutation (partial map);
// one `append` op pushes a single [label, value] slice. Class-level
// defaults (slices, colors, inner_radius, show_labels, show_legend,
// total_label) ride in on the mount field `props` and seed the slice.

import { Cell, Legend, Pie, PieChart as RcPieChart, ResponsiveContainer, Tooltip } from "recharts";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

type Slice = { label: string; value: number };
type PieChartValue = { slices: Slice[] };

const DEFAULT_COLORS = [
	"#2563eb",
	"#16a34a",
	"#f59e0b",
	"#dc2626",
	"#7c3aed",
	"#0891b2",
	"#db2777",
	"#65a30d",
];

const DEFAULTS = {
	colors: DEFAULT_COLORS,
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
	if (!Array.isArray(v) || v.length === 0) return DEFAULT_COLORS;
	const out = v.filter((c): c is string => typeof c === "string");
	return out.length === 0 ? DEFAULT_COLORS : out;
}

// Accepts a {slices: [...]} map, a [[label, value], ...] pairs list, or a
// flat [v0, v1, ...] list (auto-labeled "0".."n-1"). Anything else -> [].
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
			if ("slices" in p) {
				slice.value = { slices: _toSlices(p.slices) };
			}
			if ("colors" in p) {
				slice.colors = _colors(p.colors);
			}
			if ("inner_radius" in p) {
				slice.inner_radius = _radius(p.inner_radius);
			}
			if ("show_labels" in p) {
				slice.show_labels = _bool(p.show_labels, DEFAULTS.show_labels);
			}
			if ("show_legend" in p) {
				slice.show_legend = _bool(p.show_legend, DEFAULTS.show_legend);
			}
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

type LabelPayload = {
	cx?: number;
	cy?: number;
	midAngle?: number;
	innerRadius?: number;
	outerRadius?: number;
	label?: string;
};

function _renderLabel(props: LabelPayload): string {
	return props.label ?? "";
}

function CenterText({ label, total }: { label: string; total: number }) {
	return (
		<g>
			<text
				x="50%"
				y="50%"
				dy={-6}
				textAnchor="middle"
				dominantBaseline="middle"
				className="fill-current text-xs"
			>
				{label}
			</text>
			<text
				x="50%"
				y="50%"
				dy={12}
				textAnchor="middle"
				dominantBaseline="middle"
				className="fill-current text-sm font-medium"
			>
				{total}
			</text>
		</g>
	);
}

function PieChartView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as PieChartValue | undefined);
	const colors = useStore((s) => (s.refs[path]?.colors as string[]) ?? DEFAULT_COLORS);
	const inner_radius = useStore((s) => (s.refs[path]?.inner_radius as number) ?? 0);
	const show_labels = useStore((s) => (s.refs[path]?.show_labels as boolean) ?? true);
	const show_legend = useStore((s) => (s.refs[path]?.show_legend as boolean) ?? true);
	const total_label = useStore((s) => (s.refs[path]?.total_label as string) ?? "");
	const slices = Array.isArray(value?.slices) ? value.slices : [];
	const total = slices.reduce((a, s) => a + (Number.isFinite(s.value) ? s.value : 0), 0);
	const innerPct = `${Math.round(inner_radius * 80)}%`;
	const showCenter = inner_radius > 0 && total_label.length > 0;
	return (
		<div className="h-64 w-full">
			<ResponsiveContainer width="100%" height="100%">
				<RcPieChart>
					<Pie
						data={slices}
						dataKey="value"
						nameKey="label"
						innerRadius={innerPct}
						outerRadius="80%"
						isAnimationActive={false}
						label={show_labels ? (_renderLabel as never) : false}
					>
						{slices.map((s, i) => (
							<Cell key={s.label || `slice-${i}`} fill={colors[i % colors.length]} />
						))}
					</Pie>
					<Tooltip />
					{show_legend && <Legend />}
					{showCenter && <CenterText label={total_label} total={total} />}
				</RcPieChart>
			</ResponsiveContainer>
		</div>
	);
}

export const PieChart: RefEntry = { factory, component: PieChartView };
