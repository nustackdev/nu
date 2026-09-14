// BarChart -- display-only categorical bar chart.
//
// Server-owned. Chrome (x_label, y_label, color, orientation, max_bars) is
// plain props, declared at the slot and coerced where it is read. The bars
// live on `value` as {bars: [[category, value], ...]}.
//
// Two handlers. `write` carries a partial map whose `bars` needs shape
// coercion (maps, pairs, or bare values all arrive on the same key) and a
// trim against the current window, neither of which the default write does.
// `append` upserts a single bar by category, which is not a write at all.
// Composes the kit BarChart primitive; the primitive owns chrome via
// chart-shared tokens.

import { BarChart as KitBarChart } from "../../components/ui/bar-chart";
import { type NodeEntry, type NodeProps, useStringProp, useValue } from "../../tree";

type Bar2 = [string, number | null];
type BarChartValue = { bars: Bar2[] };
type Orientation = "vertical" | "horizontal";

const DEFAULTS = {
	x_label: "",
	y_label: "",
	color: "",
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

// A write payload that is not a map carries nothing this type understands.
function _map(v: unknown): Record<string, unknown> {
	return v != null && typeof v === "object" && !Array.isArray(v)
		? (v as Record<string, unknown>)
		: {};
}

function _bars(v: unknown): Bar2[] {
	const cur = v as BarChartValue | undefined | null;
	return Array.isArray(cur?.bars) ? (cur.bars as Bar2[]) : [];
}

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

function BarChartView({ path }: NodeProps) {
	const value = useValue<unknown>(path, null);
	const color = useStringProp(path, "color", DEFAULTS.color);
	const bars = _bars(value);
	const data = bars.map((b) => ({
		x: Array.isArray(b) ? _cat(b[0], 0) : "",
		y: Array.isArray(b) ? _y(b[1]) : null,
	}));
	const series = color
		? [{ dataKey: "y", name: "value", color }]
		: [{ dataKey: "y", name: "value" }];
	return <KitBarChart data={data} series={series} xKey="x" height={256} showLegend={false} />;
}

export const BarChart: NodeEntry = {
	component: BarChartView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				const p = _map(payload);
				if ("x_label" in p) props.x_label = p.x_label == null ? "" : String(p.x_label);
				if ("y_label" in p) props.y_label = p.y_label == null ? "" : String(p.y_label);
				if ("color" in p) {
					if (typeof p.color === "string") props.color = p.color;
				}
				if ("orientation" in p) props.orientation = _orient(p.orientation);
				if ("max_bars" in p) props.max_bars = _cap(p.max_bars);
				const cap = _cap(props.max_bars);
				if ("bars" in p) {
					props.value = { bars: _trim(_toBars(p.bars), cap) };
					return;
				}
				const bars = _bars(props.value);
				if (bars.length > cap) props.value = { bars: _trim(bars, cap) };
			}),
		append: (ctx, payload) =>
			ctx.update((props) => {
				const bars = [..._bars(props.value)];
				if (Array.isArray(payload) && payload.length === 2) {
					const cat = _cat(payload[0], bars.length);
					const val = _y(payload[1]);
					const idx = bars.findIndex(([c]) => c === cat);
					if (idx >= 0) {
						bars[idx] = [cat, val];
					} else {
						bars.push([cat, val]);
					}
				}
				props.value = { bars: _trim(bars, _cap(props.max_bars)) };
			}),
	},
};
