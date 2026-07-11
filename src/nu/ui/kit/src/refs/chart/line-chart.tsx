// LineChart -- display-only time-series chart, recharts.
//
// Server-owned. One `write` op carries every mutation (partial map);
// one `append` op pushes a single [x, y] point or a {name, x, y} row in
// multi-series mode. Class-level defaults (x_label, y_label, color,
// max_points, x_format, show_legend, show_tooltip, palette) ride in on
// the mount field `props` and seed the slice.
//
// Single-series wire payload (legacy): {points: [[x, y], ...]}.
// Multi-series wire payload: {series: [{name, points: [[x, y], ...], color?}, ...]}.
// The renderer auto-detects which shape is present on the slice value.

import {
	CartesianGrid,
	Legend,
	Line,
	LineChart as RcLineChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

// A point's y may be null: the server resolved that sample to a Nu
// sentinel (EMPTY / INVALID). recharts draws a gap for a null y.
type Point = [number, number | null];
type Series = { name: string; points: Point[]; color?: string };
// Slice value carries either single-series points or a multi-series list.
type LineChartValue = { points?: Point[]; series?: Series[] };

const DEFAULTS = {
	x_label: "",
	y_label: "",
	color: "#2563eb",
	max_points: 500,
	x_format: "number" as "number" | "time",
	show_legend: false,
	show_tooltip: true,
	palette: [] as string[],
};

function _num(v: unknown, fallback: number): number {
	return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

function _y(v: unknown): number | null {
	return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function _cap(n: unknown): number {
	const v = Number(n);
	if (!Number.isFinite(v)) return DEFAULTS.max_points;
	return v < 1 ? 1 : Math.floor(v);
}

function _fmt(v: unknown): "number" | "time" {
	return v === "time" ? "time" : "number";
}

function _strList(v: unknown): string[] {
	if (!Array.isArray(v)) return [];
	return v.filter((e): e is string => typeof e === "string");
}

// Accepts either a {points: [...]} map, a [[x, y], ...] pairs list, or
// a flat [y, y, ...] list (auto-x = 0..n-1). Anything else -> [].
function _toPoints(v: unknown): Point[] {
	if (v && typeof v === "object" && !Array.isArray(v) && "points" in v) {
		return _toPoints((v as { points: unknown }).points);
	}
	if (Array.isArray(v)) {
		if (v.length === 0) return [];
		const pairs = v.every((e) => Array.isArray(e) && (e as unknown[]).length === 2);
		if (pairs) {
			return (v as unknown[][]).map((p, i) => [_num(p[0], i), _y(p[1])]);
		}
		return v.map((y, i) => [i, _y(y)]);
	}
	return [];
}

function _toSeries(v: unknown): Series[] {
	if (!Array.isArray(v)) return [];
	const out: Series[] = [];
	for (let i = 0; i < v.length; i++) {
		const s = v[i];
		if (!s || typeof s !== "object") continue;
		const obj = s as Record<string, unknown>;
		const name = typeof obj.name === "string" ? obj.name : `s${i}`;
		const points = _toPoints(obj.points);
		const entry: Series = { name, points };
		if (typeof obj.color === "string") entry.color = obj.color;
		out.push(entry);
	}
	return out;
}

function _trim(pts: Point[], cap: number): Point[] {
	if (pts.length <= cap) return pts;
	return pts.slice(pts.length - cap);
}

function _trimSeries(list: Series[], cap: number): Series[] {
	return list.map((s) => ({ ...s, points: _trim(s.points, cap) }));
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "LineChart",
	value: { points: [] } as LineChartValue,
	x_label: typeof props?.x_label === "string" ? (props.x_label as string) : DEFAULTS.x_label,
	y_label: typeof props?.y_label === "string" ? (props.y_label as string) : DEFAULTS.y_label,
	color: typeof props?.color === "string" ? (props.color as string) : DEFAULTS.color,
	max_points: typeof props?.max_points === "number" ? _cap(props.max_points) : DEFAULTS.max_points,
	x_format: _fmt(props?.x_format),
	show_legend:
		typeof props?.show_legend === "boolean" ? (props.show_legend as boolean) : DEFAULTS.show_legend,
	show_tooltip:
		typeof props?.show_tooltip === "boolean"
			? (props.show_tooltip as boolean)
			: DEFAULTS.show_tooltip,
	palette: _strList(props?.palette),
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
			if ("max_points" in p) {
				slice.max_points = _cap(p.max_points);
			}
			if ("x_format" in p) {
				slice.x_format = _fmt(p.x_format);
			}
			if ("show_legend" in p) {
				slice.show_legend = Boolean(p.show_legend);
			}
			if ("show_tooltip" in p) {
				slice.show_tooltip = Boolean(p.show_tooltip);
			}
			if ("palette" in p) {
				slice.palette = _strList(p.palette);
			}
			const cap = (slice.max_points as number) ?? DEFAULTS.max_points;
			if ("series" in p) {
				slice.value = { series: _trimSeries(_toSeries(p.series), cap) };
			} else if ("points" in p) {
				slice.value = { points: _trim(_toPoints(p.points), cap) };
			} else {
				// max_points may have shrunk; re-trim the existing buffer.
				const cur = slice.value as LineChartValue | undefined;
				if (cur?.series) {
					slice.value = { series: _trimSeries(cur.series, cap) };
				} else {
					const pts = Array.isArray(cur?.points) ? (cur?.points as Point[]) : [];
					if (pts.length > cap) slice.value = { points: _trim(pts, cap) };
				}
			}
		}),
	append: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const cur = slice.value as LineChartValue | undefined;
			const cap = (slice.max_points as number) ?? DEFAULTS.max_points;
			// Multi-series append: {name, x, y} touches one named series.
			if (v && typeof v === "object" && !Array.isArray(v) && "name" in (v as object)) {
				const obj = v as Record<string, unknown>;
				const name = typeof obj.name === "string" ? obj.name : "";
				if (!name) return;
				const list = Array.isArray(cur?.series) ? [...(cur?.series as Series[])] : [];
				const idx = list.findIndex((s) => s.name === name);
				const pt: Point = [_num(obj.x, 0), _y(obj.y)];
				if (idx === -1) {
					list.push({ name, points: [pt] });
				} else {
					const next = [...list[idx].points, pt];
					list[idx] = { ...list[idx], points: _trim(next, cap) };
				}
				slice.value = { series: list.map((s) => ({ ...s, points: _trim(s.points, cap) })) };
				return;
			}
			// Single-series append: [x, y].
			const pts = Array.isArray(cur?.points) ? [...(cur?.points as Point[])] : [];
			if (Array.isArray(v) && v.length === 2) {
				pts.push([_num(v[0], pts.length), _y(v[1])]);
			}
			slice.value = { points: _trim(pts, cap) };
		}),
});

function _pad2(n: number): string {
	return n < 10 ? `0${n}` : String(n);
}

function _timeTick(v: number): string {
	const d = new Date(v);
	if (Number.isNaN(d.getTime())) return String(v);
	return `${_pad2(d.getHours())}:${_pad2(d.getMinutes())}:${_pad2(d.getSeconds())}`;
}

function _paletteColor(palette: string[], i: number, fallback: string): string {
	if (palette.length === 0) return fallback;
	return palette[i % palette.length];
}

function LineChartView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as LineChartValue | undefined);
	const x_label = useStore((s) => (s.refs[path]?.x_label as string) ?? "");
	const y_label = useStore((s) => (s.refs[path]?.y_label as string) ?? "");
	const color = useStore((s) => (s.refs[path]?.color as string) ?? DEFAULTS.color);
	const x_format = useStore((s) => (s.refs[path]?.x_format as "number" | "time") ?? "number");
	const show_legend = useStore((s) => (s.refs[path]?.show_legend as boolean) ?? false);
	const show_tooltip = useStore((s) => (s.refs[path]?.show_tooltip as boolean) ?? true);
	const palette = useStore((s) => (s.refs[path]?.palette as string[]) ?? DEFAULTS.palette);

	const multi = Array.isArray(value?.series);
	const seriesList: Series[] = multi ? (value?.series as Series[]) : [];
	const singlePoints: Point[] = multi
		? []
		: Array.isArray(value?.points)
			? (value?.points as Point[])
			: [];

	// Build a unified data table keyed by x. For single series we keep the
	// original "y" key; for multi-series we use the series name as the key.
	const data: Record<string, number | null>[] = [];
	if (multi) {
		const byX = new Map<number, Record<string, number | null>>();
		for (let i = 0; i < seriesList.length; i++) {
			const s = seriesList[i];
			for (let k = 0; k < s.points.length; k++) {
				const p = s.points[k];
				const x = Array.isArray(p) ? _num(p[0], k) : k;
				const row = byX.get(x) ?? { x };
				row[s.name] = Array.isArray(p) ? _y(p[1]) : null;
				byX.set(x, row);
			}
		}
		const xs = Array.from(byX.keys()).sort((a, b) => a - b);
		for (const x of xs) {
			const row = byX.get(x);
			if (row) data.push(row);
		}
	} else {
		for (let i = 0; i < singlePoints.length; i++) {
			const p = singlePoints[i];
			data.push({
				x: Array.isArray(p) ? _num(p[0], i) : i,
				y: Array.isArray(p) ? _y(p[1]) : null,
			});
		}
	}

	const xTick = x_format === "time" ? _timeTick : undefined;
	const xLabelProp = x_label
		? ({ value: x_label, position: "insideBottom", offset: -2 } as const)
		: undefined;
	const yLabelProp = y_label
		? ({ value: y_label, angle: -90, position: "insideLeft" } as const)
		: undefined;
	const tooltipLabelFormatter =
		x_format === "time" ? (label: unknown) => _timeTick(label as number) : undefined;
	return (
		<div className="h-64 w-full">
			<ResponsiveContainer width="100%" height="100%">
				<RcLineChart
					data={data}
					margin={{ top: 8, right: 16, bottom: x_label ? 20 : 8, left: y_label ? 12 : 0 }}
				>
					<CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
					<XAxis
						dataKey="x"
						type="number"
						domain={["dataMin", "dataMax"]}
						tickFormatter={xTick}
						label={xLabelProp as never}
					/>
					<YAxis label={yLabelProp as never} />
					{show_tooltip ? <Tooltip labelFormatter={tooltipLabelFormatter} /> : null}
					{multi && show_legend ? <Legend /> : null}
					{multi ? (
						seriesList.map((s, i) => (
							<Line
								key={s.name}
								type="monotone"
								dataKey={s.name}
								stroke={s.color ?? _paletteColor(palette, i, DEFAULTS.color)}
								dot={false}
								isAnimationActive={false}
								connectNulls={false}
							/>
						))
					) : (
						<Line
							type="monotone"
							dataKey="y"
							stroke={color}
							dot={false}
							isAnimationActive={false}
							connectNulls={false}
						/>
					)}
				</RcLineChart>
			</ResponsiveContainer>
		</div>
	);
}

export const LineChart: RefEntry = { factory, component: LineChartView };
