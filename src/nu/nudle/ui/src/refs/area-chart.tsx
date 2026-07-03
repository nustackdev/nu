// AreaChart -- display-only area chart, recharts. Single or stacked
// multi-series with a sliding window.
//
// Server-owned. One `write` op carries every mutation (partial map);
// one `append` op pushes a single [x, y0, y1, ...] row. Class-level
// defaults (x_label, y_label, series, colors, stacked, max_points,
// x_format) ride in on the mount field `props` and seed the slice.

import {
	Area,
	CartesianGrid,
	Legend,
	AreaChart as RcAreaChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

// A row is [x, y0, y1, ...] with one y per entry in `series`.
// Either x or any y may be null (server resolved a Nu sentinel).
type Row = (number | null)[];
type AreaChartValue = { points: Row[] };

const DEFAULTS = {
	x_label: "",
	y_label: "",
	series: ["value"] as string[],
	colors: ["#2563eb"] as string[],
	stacked: false,
	max_points: 500,
	x_format: "number" as "number" | "time",
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

function _strList(v: unknown, fallback: string[]): string[] {
	if (!Array.isArray(v)) return fallback;
	return v.filter((e): e is string => typeof e === "string");
}

// Reshape a row against a series-count target: keep x, then pad with
// null or truncate the y tail so the row has exactly `1 + n` slots.
function _row(raw: unknown, n: number): Row {
	if (!Array.isArray(raw)) return [null, ...Array<null>(n).fill(null)];
	const x = raw.length > 0 ? (_num(raw[0], Number.NaN) as number) : Number.NaN;
	const head: number | null = Number.isFinite(x) ? x : null;
	const ys: (number | null)[] = [];
	for (let i = 0; i < n; i++) {
		ys.push(i + 1 < raw.length ? _y(raw[i + 1]) : null);
	}
	return [head, ...ys];
}

function _toPoints(v: unknown, n: number): Row[] {
	if (!Array.isArray(v)) return [];
	return v.map((r) => _row(r, n));
}

function _trim(pts: Row[], cap: number): Row[] {
	if (pts.length <= cap) return pts;
	return pts.slice(pts.length - cap);
}

// Re-shape an existing buffer to a new series count (truncate or null-pad
// each row's y tail). Used when `series` changes without fresh `points`.
function _reshape(pts: Row[], n: number): Row[] {
	return pts.map((r) => {
		const x = r.length > 0 ? r[0] : null;
		const ys: (number | null)[] = [];
		for (let i = 0; i < n; i++) {
			ys.push(i + 1 < r.length ? (r[i + 1] ?? null) : null);
		}
		return [x, ...ys];
	});
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "AreaChart",
	value: { points: [] } as AreaChartValue,
	x_label: typeof props?.x_label === "string" ? (props.x_label as string) : DEFAULTS.x_label,
	y_label: typeof props?.y_label === "string" ? (props.y_label as string) : DEFAULTS.y_label,
	series: _strList(props?.series, DEFAULTS.series),
	colors: _strList(props?.colors, DEFAULTS.colors),
	stacked: typeof props?.stacked === "boolean" ? (props.stacked as boolean) : DEFAULTS.stacked,
	max_points: typeof props?.max_points === "number" ? _cap(props.max_points) : DEFAULTS.max_points,
	x_format: _fmt(props?.x_format),
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
			if ("series" in p) {
				slice.series = _strList(p.series, []);
			}
			if ("colors" in p) {
				slice.colors = _strList(p.colors, slice.colors as string[]);
			}
			if ("stacked" in p) {
				slice.stacked = Boolean(p.stacked);
			}
			if ("max_points" in p) {
				slice.max_points = _cap(p.max_points);
			}
			if ("x_format" in p) {
				slice.x_format = _fmt(p.x_format);
			}
			const n = (slice.series as string[]).length;
			const cap = (slice.max_points as number) ?? DEFAULTS.max_points;
			if ("points" in p) {
				slice.value = { points: _trim(_toPoints(p.points, n), cap) };
			} else {
				const cur = slice.value as AreaChartValue | undefined;
				let pts = Array.isArray(cur?.points) ? (cur?.points as Row[]) : [];
				if ("series" in p) pts = _reshape(pts, n);
				if (pts.length > cap) pts = _trim(pts, cap);
				if ("series" in p || pts !== cur?.points) slice.value = { points: pts };
			}
		}),
	append: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			if (!Array.isArray(v) || v.length < 1) return;
			const n = (slice.series as string[]).length;
			if (n === 0) return;
			const cur = slice.value as AreaChartValue | undefined;
			const pts = Array.isArray(cur?.points) ? [...(cur?.points as Row[])] : [];
			pts.push(_row(v, n));
			const cap = (slice.max_points as number) ?? DEFAULTS.max_points;
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

function _color(colors: string[], i: number): string {
	if (colors.length === 0) return DEFAULTS.colors[0];
	return colors[i % colors.length];
}

function AreaChartView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as AreaChartValue | undefined);
	const x_label = useStore((s) => (s.refs[path]?.x_label as string) ?? "");
	const y_label = useStore((s) => (s.refs[path]?.y_label as string) ?? "");
	const series = useStore((s) => (s.refs[path]?.series as string[]) ?? DEFAULTS.series);
	const colors = useStore((s) => (s.refs[path]?.colors as string[]) ?? DEFAULTS.colors);
	const stacked = useStore((s) => (s.refs[path]?.stacked as boolean) ?? false);
	const x_format = useStore((s) => (s.refs[path]?.x_format as "number" | "time") ?? "number");
	const points = Array.isArray(value?.points) ? (value?.points as Row[]) : [];
	const data = points.map((r, i) => {
		const row: Record<string, number | null> = { x: Array.isArray(r) ? _num(r[0], i) : i };
		for (let k = 0; k < series.length; k++) {
			row[series[k]] = Array.isArray(r) ? _y(r[k + 1]) : null;
		}
		return row;
	});
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
				<RcAreaChart
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
					<Tooltip labelFormatter={tooltipLabelFormatter} />
					{series.length > 1 ? <Legend /> : null}
					{series.map((name, i) => {
						const c = _color(colors, i);
						return (
							<Area
								key={name}
								type="monotone"
								dataKey={name}
								stroke={c}
								fill={c}
								fillOpacity={0.25}
								stackId={stacked ? "s" : undefined}
								dot={false}
								isAnimationActive={false}
								connectNulls={false}
							/>
						);
					})}
				</RcAreaChart>
			</ResponsiveContainer>
		</div>
	);
}

export const AreaChart: RefEntry = { factory, component: AreaChartView };
