// BarChart -- display-only categorical bar chart, recharts.
//
// Server-owned. One `write` op carries every mutation (partial map);
// one `append` op upserts a single [category, value] bar. Class-level
// defaults (x_label, y_label, color, orientation, max_bars) ride in on
// the mount field `props` and seed the slice.

import {
	Bar,
	CartesianGrid,
	BarChart as RcBarChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

// A bar's value may be null: the server resolved that sample to a Nu
// sentinel (EMPTY / INVALID). null bars render as a gap (no bar drawn,
// the category label stays).
type Bar2 = [string, number | null];
type BarChartValue = { bars: Bar2[] };
type Orientation = "vertical" | "horizontal";

const DEFAULTS = {
	x_label: "",
	y_label: "",
	color: "#2563eb",
	orientation: "vertical" as Orientation,
	max_bars: 200,
};

function _y(v: unknown): number | null {
	return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function _cap(n: unknown): number {
	const v = Number(n);
	if (!Number.isFinite(v)) return DEFAULTS.max_bars;
	return v < 1 ? 1 : Math.floor(v);
}

function _orient(v: unknown): Orientation {
	return v === "horizontal" ? "horizontal" : "vertical";
}

function _cat(v: unknown, i: number): string {
	if (v == null) return String(i);
	return String(v);
}

// Accepts a {bars: [...]} map, a [[category, value], ...] pairs list,
// a list of {label, value} maps, or a flat [v0, v1, ...] list
// (auto-category = "0".."n-1"). Anything else -> [].
// On dup categories: last write wins (later entries replace earlier).
function _toBars(v: unknown): Bar2[] {
	if (v && typeof v === "object" && !Array.isArray(v) && "bars" in v) {
		return _toBars((v as { bars: unknown }).bars);
	}
	if (!Array.isArray(v)) return [];
	if (v.length === 0) return [];
	const pairs: Bar2[] = [];
	const maps = v.every(
		(e) => e && typeof e === "object" && !Array.isArray(e) && "label" in (e as object),
	);
	if (maps) {
		(v as Array<{ label: unknown; value: unknown }>).forEach((e, i) => {
			pairs.push([_cat(e.label, i), _y(e.value)]);
		});
	} else {
		const tuples = v.every((e) => Array.isArray(e) && (e as unknown[]).length === 2);
		if (tuples) {
			(v as unknown[][]).forEach((p, i) => {
				pairs.push([_cat(p[0], i), _y(p[1])]);
			});
		} else {
			v.forEach((val, i) => {
				pairs.push([String(i), _y(val)]);
			});
		}
	}
	// dedup by category, last wins, preserving last occurrence order.
	const seen = new Map<string, number>();
	pairs.forEach(([cat], idx) => {
		seen.set(cat, idx);
	});
	const out: Bar2[] = [];
	pairs.forEach(([cat, val], idx) => {
		if (seen.get(cat) === idx) out.push([cat, val]);
	});
	return out;
}

function _trim(bars: Bar2[], cap: number): Bar2[] {
	if (bars.length <= cap) return bars;
	return bars.slice(bars.length - cap);
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "BarChart",
	value: { bars: [] } as BarChartValue,
	x_label: typeof props?.x_label === "string" ? (props.x_label as string) : DEFAULTS.x_label,
	y_label: typeof props?.y_label === "string" ? (props.y_label as string) : DEFAULTS.y_label,
	color: typeof props?.color === "string" ? (props.color as string) : DEFAULTS.color,
	orientation: _orient(props?.orientation),
	max_bars: typeof props?.max_bars === "number" ? _cap(props.max_bars) : DEFAULTS.max_bars,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as Record<string, unknown>;
			if ("x_label" in p) {
				slice.x_label = p.x_label == null ? "" : String(p.x_label);
			}
			if ("y_label" in p) {
				slice.y_label = p.y_label == null ? "" : String(p.y_label);
			}
			if ("color" in p) {
				if (typeof p.color === "string") slice.color = p.color;
			}
			if ("orientation" in p) {
				slice.orientation = _orient(p.orientation);
			}
			if ("max_bars" in p) {
				slice.max_bars = _cap(p.max_bars);
			}
			if ("bars" in p) {
				const cap = (slice.max_bars as number) ?? DEFAULTS.max_bars;
				slice.value = { bars: _trim(_toBars(p.bars), cap) };
			} else {
				const cur = slice.value as BarChartValue | undefined;
				const bars = Array.isArray(cur?.bars) ? cur.bars : [];
				const cap = (slice.max_bars as number) ?? DEFAULTS.max_bars;
				if (bars.length > cap) slice.value = { bars: _trim(bars, cap) };
			}
		}),
	append: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const cur = slice.value as BarChartValue | undefined;
			const bars = Array.isArray(cur?.bars) ? [...cur.bars] : [];
			if (Array.isArray(v) && v.length === 2) {
				const cat = _cat(v[0], bars.length);
				const val = _y(v[1]);
				const idx = bars.findIndex(([c]) => c === cat);
				if (idx >= 0) {
					bars[idx] = [cat, val];
				} else {
					bars.push([cat, val]);
				}
			}
			const cap = (slice.max_bars as number) ?? DEFAULTS.max_bars;
			slice.value = { bars: _trim(bars, cap) };
		}),
});

function BarChartView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as BarChartValue | undefined);
	const x_label = useStore((s) => (s.refs[path]?.x_label as string) ?? "");
	const y_label = useStore((s) => (s.refs[path]?.y_label as string) ?? "");
	const color = useStore((s) => (s.refs[path]?.color as string) ?? DEFAULTS.color);
	const orientation = useStore(
		(s) => (s.refs[path]?.orientation as Orientation) ?? DEFAULTS.orientation,
	);
	const bars = Array.isArray(value?.bars) ? value.bars : [];
	const data = bars.map((b, i) => ({
		x: Array.isArray(b) ? _cat(b[0], i) : String(i),
		y: Array.isArray(b) ? _y(b[1]) : null,
	}));
	const isHorizontal = orientation === "horizontal";
	const xLabelProp = x_label
		? ({ value: x_label, position: "insideBottom", offset: -2 } as const)
		: undefined;
	const yLabelProp = y_label
		? ({ value: y_label, angle: -90, position: "insideLeft" } as const)
		: undefined;
	return (
		<div className="h-64 w-full">
			<ResponsiveContainer width="100%" height="100%">
				<RcBarChart
					data={data}
					layout={isHorizontal ? "vertical" : "horizontal"}
					margin={{
						top: 8,
						right: 16,
						bottom: x_label ? 20 : 8,
						left: y_label ? 12 : 0,
					}}
				>
					<CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
					{isHorizontal ? (
						<>
							<XAxis type="number" label={xLabelProp as never} />
							<YAxis type="category" dataKey="x" label={yLabelProp as never} />
						</>
					) : (
						<>
							<XAxis dataKey="x" type="category" label={xLabelProp as never} />
							<YAxis type="number" label={yLabelProp as never} />
						</>
					)}
					<Tooltip />
					<Bar dataKey="y" fill={color} isAnimationActive={false} />
				</RcBarChart>
			</ResponsiveContainer>
		</div>
	);
}

export const BarChart: RefEntry = { factory, component: BarChartView };
