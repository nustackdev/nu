// AreaChart -- display-only area chart. Single or stacked multi-series with
// a sliding window.
//
// Server-owned. One `write` op carries every mutation (partial map);
// one `append` op pushes a single [x, y0, y1, ...] row. Class-level
// defaults (x_label, y_label, series, colors, stacked, max_points,
// x_format) ride in on the mount field `props` and seed the slice.
// Composes the kit AreaChart primitive; the primitive owns chart chrome
// (grid, ticks, tooltip) via chart-shared tokens. Series colors come from
// the categorical palette (var(--chart-N)) unless the slice overrides.

import { AreaChart as KitAreaChart } from "../../components/ui/area-chart";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

// A row is [x, y0, y1, ...] with one y per entry in `series`.
type Row = (number | null)[];
type AreaChartValue = { points: Row[] };
type XFormat = "number" | "time" | "datetime_us" | "datetime_ms" | "datetime_s";
const X_FORMATS: readonly XFormat[] = [
	"number",
	"time",
	"datetime_us",
	"datetime_ms",
	"datetime_s",
];

const DEFAULTS = {
	x_label: "",
	y_label: "",
	series: ["value"] as string[],
	colors: [] as string[],
	stacked: false,
	max_points: 500,
	x_format: "number" as XFormat,
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

function _fmt(v: unknown): XFormat {
	return typeof v === "string" && (X_FORMATS as readonly string[]).includes(v)
		? (v as XFormat)
		: "number";
}

function _strList(v: unknown, fallback: string[]): string[] {
	if (!Array.isArray(v)) return fallback;
	return v.filter((e): e is string => typeof e === "string");
}

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

function _pad2(n: number): string {
	return n < 10 ? `0${n}` : String(n);
}

function _pad3(n: number): string {
	return n < 10 ? `00${n}` : n < 100 ? `0${n}` : String(n);
}

function _fmtTick(v: number, fmt: XFormat): string | number {
	if (fmt === "number") return v;
	let ms: number;
	if (fmt === "datetime_us") ms = v / 1000;
	else if (fmt === "datetime_s") ms = v * 1000;
	else ms = v;
	const d = new Date(ms);
	if (Number.isNaN(d.getTime())) return String(v);
	const hh = _pad2(d.getHours());
	const mm = _pad2(d.getMinutes());
	const ss = _pad2(d.getSeconds());
	if (fmt === "datetime_us" || fmt === "datetime_ms") {
		return `${hh}:${mm}:${ss}.${_pad3(d.getMilliseconds())}`;
	}
	return `${hh}:${mm}:${ss}`;
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
			if ("x_label" in p) slice.x_label = p.x_label == null ? "" : String(p.x_label);
			if ("y_label" in p) slice.y_label = p.y_label == null ? "" : String(p.y_label);
			if ("series" in p) slice.series = _strList(p.series, []);
			if ("colors" in p) slice.colors = _strList(p.colors, slice.colors as string[]);
			if ("stacked" in p) slice.stacked = Boolean(p.stacked);
			if ("max_points" in p) slice.max_points = _cap(p.max_points);
			if ("x_format" in p) slice.x_format = _fmt(p.x_format);
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

function AreaChartView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as AreaChartValue | undefined);
	const series = useStore((s) => (s.refs[path]?.series as string[]) ?? DEFAULTS.series);
	const colors = useStore((s) => (s.refs[path]?.colors as string[]) ?? DEFAULTS.colors);
	const stacked = useStore((s) => (s.refs[path]?.stacked as boolean) ?? false);
	const x_format = useStore((s) => (s.refs[path]?.x_format as XFormat) ?? "number");
	const points = Array.isArray(value?.points) ? (value?.points as Row[]) : [];
	const data = points.map((r, i) => {
		const raw = Array.isArray(r) ? _num(r[0], i) : i;
		const x = _fmtTick(raw, x_format);
		const row: Record<string, number | string | null> = { x };
		for (let k = 0; k < series.length; k++) {
			row[series[k]] = Array.isArray(r) ? _y(r[k + 1]) : null;
		}
		return row;
	});
	const seriesList = series.map((name, i) => {
		const color = colors[i];
		return color ? { dataKey: name, name, color } : { dataKey: name, name };
	});
	return (
		<KitAreaChart
			data={data}
			series={seriesList}
			xKey="x"
			height={256}
			stacked={stacked}
			showLegend={series.length > 1}
		/>
	);
}

export const AreaChart: RefEntry = { factory, component: AreaChartView };
