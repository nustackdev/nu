// LineChart -- display-only time-series chart, recharts.
//
// Server-owned. One `write` op carries every mutation (partial map);
// one `append` op pushes a single [x, y] point. Class-level defaults
// (x_label, y_label, color, max_points, x_format) ride in on the
// mount field `props` and seed the slice.

import {
	CartesianGrid,
	Line,
	LineChart as RcLineChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

// A point's y may be null: the server resolved that sample to a Nu
// sentinel (EMPTY / INVALID). recharts draws a gap for a null y.
type Point = [number, number | null];
type LineChartValue = { points: Point[] };

const DEFAULTS = {
	x_label: "",
	y_label: "",
	color: "#2563eb",
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

function _trim(pts: Point[], cap: number): Point[] {
	if (pts.length <= cap) return pts;
	return pts.slice(pts.length - cap);
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "LineChart",
	value: { points: [] } as LineChartValue,
	x_label: typeof props?.x_label === "string" ? (props.x_label as string) : DEFAULTS.x_label,
	y_label: typeof props?.y_label === "string" ? (props.y_label as string) : DEFAULTS.y_label,
	color: typeof props?.color === "string" ? (props.color as string) : DEFAULTS.color,
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
			if ("color" in p) {
				if (typeof p.color === "string") slice.color = p.color;
			}
			if ("max_points" in p) {
				slice.max_points = _cap(p.max_points);
			}
			if ("x_format" in p) {
				slice.x_format = _fmt(p.x_format);
			}
			if ("points" in p) {
				const cap = (slice.max_points as number) ?? DEFAULTS.max_points;
				slice.value = { points: _trim(_toPoints(p.points), cap) };
			} else {
				// max_points may have shrunk; re-trim the existing buffer.
				const cur = slice.value as LineChartValue | undefined;
				const pts = Array.isArray(cur?.points) ? cur.points : [];
				const cap = (slice.max_points as number) ?? DEFAULTS.max_points;
				if (pts.length > cap) slice.value = { points: _trim(pts, cap) };
			}
		}),
	append: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const cur = slice.value as LineChartValue | undefined;
			const pts = Array.isArray(cur?.points) ? [...cur.points] : [];
			if (Array.isArray(v) && v.length === 2) {
				pts.push([_num(v[0], pts.length), _y(v[1])]);
			}
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

function LineChartView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as LineChartValue | undefined);
	const x_label = useStore((s) => (s.refs[path]?.x_label as string) ?? "");
	const y_label = useStore((s) => (s.refs[path]?.y_label as string) ?? "");
	const color = useStore((s) => (s.refs[path]?.color as string) ?? DEFAULTS.color);
	const x_format = useStore((s) => (s.refs[path]?.x_format as "number" | "time") ?? "number");
	const points = Array.isArray(value?.points) ? value.points : [];
	const data = points.map((p, i) => ({
		x: Array.isArray(p) ? _num(p[0], i) : i,
		y: Array.isArray(p) ? _y(p[1]) : null,
	}));
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
					<Tooltip labelFormatter={tooltipLabelFormatter} />
					<Line
						type="monotone"
						dataKey="y"
						stroke={color}
						dot={false}
						isAnimationActive={false}
						connectNulls={false}
					/>
				</RcLineChart>
			</ResponsiveContainer>
		</div>
	);
}

export const LineChart: RefEntry = { factory, component: LineChartView };
