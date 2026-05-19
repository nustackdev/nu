// LineChart -- time-series, recharts.

import {
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

function _num(v: unknown, fallback: number): number {
	return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

function _y(v: unknown): number | null {
	return typeof v === "number" && Number.isFinite(v) ? v : null;
}

// Server may push either a flat list of Y values (auto-x = 0..n-1) or
// a {points: [[x, y], ...]} payload. Anything malformed normalizes to an
// empty series rather than throwing. Called at write time.
function _toPoints(v: unknown): Point[] {
	if (Array.isArray(v)) {
		if (v.length === 0) return [];
		const pairs = v.every((e) => Array.isArray(e) && e.length === 2);
		if (pairs) {
			return (v as unknown[][]).map((p, i) => [_num(p[0], i), _y(p[1])]);
		}
		return v.map((y, i) => [i, _y(y)]);
	}
	if (v && typeof v === "object" && "points" in v) {
		return _toPoints((v as { points: unknown }).points);
	}
	return [];
}

const factory: SliceFactory = (path, ctx) => ({
	type: "LineChart",
	value: { points: [] } as LineChartValue,
	write: (v) =>
		ctx.set((refs) => {
			refs[path].value = { points: _toPoints(v) };
		}),
	append: (v) =>
		ctx.set((refs) => {
			const cur = refs[path].value as LineChartValue;
			const pts = Array.isArray(cur?.points) ? cur.points : [];
			if (Array.isArray(v) && v.length === 2) {
				pts.push([_num(v[0], pts.length), _y(v[1])]);
			}
			refs[path].value = { points: pts };
		}),
});

function LineChartView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as LineChartValue | undefined);
	const points = Array.isArray(value?.points) ? value.points : [];
	const data = points.map((p, i) => ({
		x: Array.isArray(p) ? _num(p[0], i) : i,
		y: Array.isArray(p) ? _y(p[1]) : null,
	}));
	return (
		<div className="h-64 w-full">
			<ResponsiveContainer width="100%" height="100%">
				<RcLineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
					<XAxis dataKey="x" type="number" domain={["dataMin", "dataMax"]} />
					<YAxis />
					<Tooltip />
					<Line type="monotone" dataKey="y" dot={false} isAnimationActive={false} connectNulls />
				</RcLineChart>
			</ResponsiveContainer>
		</div>
	);
}

export const LineChart: RefEntry = { factory, component: LineChartView };
