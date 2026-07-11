// Sparkline -- display-only inline trend line.
//
// Server-owned. One `write` op carries every mutation (partial map);
// one `append` op pushes a single [x, y] point. Class-level defaults
// (color, height, max_points) ride in on the mount field `props` and
// seed the slice. Composes the kit Sparkline primitive; no axes, tooltip,
// grid, or legend.

import { Sparkline as KitSparkline } from "../../components/ui/sparkline";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

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
	type: "Sparkline",
	value: { points: [] } as SparklineValue,
	color: typeof props?.color === "string" ? (props.color as string) : DEFAULTS.color,
	height: _height(props?.height),
	max_points: _cap(props?.max_points, DEFAULTS.max_points),
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as Record<string, unknown>;
			if ("color" in p) {
				if (typeof p.color === "string") slice.color = p.color;
			}
			if ("height" in p) slice.height = _height(p.height);
			if ("max_points" in p) slice.max_points = _cap(p.max_points, DEFAULTS.max_points);
			const cap = (slice.max_points as number) ?? DEFAULTS.max_points;
			if ("points" in p) {
				slice.value = { points: _trim(_toPoints(p.points), cap) };
			} else {
				const cur = slice.value as SparklineValue | undefined;
				const pts = Array.isArray(cur?.points) ? cur.points : [];
				if (pts.length > cap) slice.value = { points: _trim(pts, cap) };
			}
		}),
	append: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const cur = slice.value as SparklineValue | undefined;
			const pts = Array.isArray(cur?.points) ? [...cur.points] : [];
			if (Array.isArray(v) && v.length === 2) {
				pts.push([_num(v[0], pts.length), _y(v[1])]);
			} else {
				return;
			}
			const cap = (slice.max_points as number) ?? DEFAULTS.max_points;
			slice.value = { points: _trim(pts, cap) };
		}),
});

function SparklineView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as SparklineValue | undefined);
	const color = useStore((s) => (s.refs[path]?.color as string) ?? DEFAULTS.color);
	const height = useStore((s) => (s.refs[path]?.height as number) ?? DEFAULTS.height);
	const points = Array.isArray(value?.points) ? value.points : [];
	// Kit Sparkline takes a bare number[]; null y renders as a gap via recharts.
	const data = points.map((p) => (Array.isArray(p) ? _y(p[1]) ?? Number.NaN : Number.NaN));
	return <KitSparkline data={data} color={color || undefined} height={height} />;
}

export const Sparkline: RefEntry = { factory, component: SparklineView };
