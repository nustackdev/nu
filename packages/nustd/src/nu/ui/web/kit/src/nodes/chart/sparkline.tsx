// Sparkline -- display-only inline trend line.
//
// Server-owned. Chrome (color, height, max_points) is plain props, declared
// at the slot and coerced where it is read. The points live on `value` as
// {points: [[x, y], ...]}.
//
// Two handlers. `write` carries a partial map whose `points` needs shape
// coercion (pairs or bare y values on the same key) and a trim against the
// current window. `append` pushes one point and re-trims. Composes the kit
// Sparkline primitive; no axes, tooltip, grid, or legend.

import { Sparkline as KitSparkline } from "../../components/ui/sparkline";
import { type NodeEntry, type NodeProps, useProp, useStringProp, useValue } from "../../tree";

type Point = [number, number | null];
type SparklineValue = { points: Point[] };

const DEFAULTS = {
	color: "",
	height: 32,
	max_points: 100,
};

function _num(v: unknown, fallback: number): number {
	return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

function _y(v: unknown): number | null {
	return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function _cap(n: unknown, fallback: number): number {
	const v = Number(n);
	if (!Number.isFinite(v)) return fallback;
	return v < 1 ? 1 : Math.floor(v);
}

function _height(n: unknown): number {
	const v = Number(n);
	if (!Number.isFinite(v)) return DEFAULTS.height;
	return v < 8 ? 8 : Math.floor(v);
}

// A write payload that is not a map carries nothing this type understands.
function _map(v: unknown): Record<string, unknown> {
	return v != null && typeof v === "object" && !Array.isArray(v)
		? (v as Record<string, unknown>)
		: {};
}

function _current(v: unknown): Point[] {
	const cur = v as SparklineValue | undefined | null;
	return Array.isArray(cur?.points) ? (cur.points as Point[]) : [];
}

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

function SparklineView({ path }: NodeProps) {
	const points = _current(useValue<unknown>(path, null));
	const color = useStringProp(path, "color", DEFAULTS.color);
	const height = _height(useProp<unknown>(path, "height", undefined));
	// Kit Sparkline takes a bare number[]; null y renders as a gap via recharts.
	const data = points.map((p) => (Array.isArray(p) ? (_y(p[1]) ?? Number.NaN) : Number.NaN));
	return <KitSparkline data={data} color={color || undefined} height={height} />;
}

export const Sparkline: NodeEntry = {
	component: SparklineView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				const p = _map(payload);
				if ("color" in p) {
					if (typeof p.color === "string") props.color = p.color;
				}
				if ("height" in p) props.height = _height(p.height);
				if ("max_points" in p) props.max_points = _cap(p.max_points, DEFAULTS.max_points);
				const cap = _cap(props.max_points, DEFAULTS.max_points);
				if ("points" in p) {
					props.value = { points: _trim(_toPoints(p.points), cap) };
					return;
				}
				const pts = _current(props.value);
				if (pts.length > cap) props.value = { points: _trim(pts, cap) };
			}),
		append: (ctx, payload) =>
			ctx.update((props) => {
				if (!Array.isArray(payload) || payload.length !== 2) return;
				const pts = [..._current(props.value)];
				pts.push([_num(payload[0], pts.length), _y(payload[1])]);
				props.value = { points: _trim(pts, _cap(props.max_points, DEFAULTS.max_points)) };
			}),
	},
};
