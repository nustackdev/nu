// AreaChart -- display-only area chart. Single or stacked multi-series with
// a sliding window.
//
// Server-owned. Chrome (x_label, y_label, series, colors, stacked,
// max_points, x_format) is plain props, declared at the slot and coerced
// where it is read. The rows live on `value` as {points: [[x, y0, y1, ...]]},
// one y per entry in `series`.
//
// Two handlers, both doing what the default write cannot. `write` carries a
// partial map that has to be normalized against the current shape: a new
// `series` reshapes every row it already holds, a smaller `max_points`
// trims the window. `append` is not a write at all -- it pushes one row and
// re-trims. Composes the kit AreaChart primitive; the primitive owns chart
// chrome (grid, ticks, tooltip) via chart-shared tokens. Series colors come
// from the categorical palette (var(--chart-N)) unless the props override.

import { AreaChart as KitAreaChart } from "../../components/ui/area-chart";
import { type NodeEntry, type NodeProps, useProp, useValue } from "../../tree";

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

// A write payload that is not a map carries nothing this type understands.
function _map(v: unknown): Record<string, unknown> {
	return v != null && typeof v === "object" && !Array.isArray(v)
		? (v as Record<string, unknown>)
		: {};
}

function _points(v: unknown): Row[] {
	const cur = v as AreaChartValue | undefined | null;
	return Array.isArray(cur?.points) ? (cur.points as Row[]) : [];
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

function AreaChartView({ path }: NodeProps) {
	const value = useValue<unknown>(path, null);
	const series = _strList(useProp<unknown>(path, "series", undefined), DEFAULTS.series);
	const colors = _strList(useProp<unknown>(path, "colors", undefined), DEFAULTS.colors);
	const stacked = useProp<unknown>(path, "stacked", undefined) === true;
	const x_format = _fmt(useProp<unknown>(path, "x_format", undefined));
	const points = _points(value);
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

export const AreaChart: NodeEntry = {
	component: AreaChartView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				const p = _map(payload);
				if ("x_label" in p) props.x_label = p.x_label == null ? "" : String(p.x_label);
				if ("y_label" in p) props.y_label = p.y_label == null ? "" : String(p.y_label);
				if ("series" in p) props.series = _strList(p.series, []);
				if ("colors" in p) {
					props.colors = _strList(p.colors, _strList(props.colors, DEFAULTS.colors));
				}
				if ("stacked" in p) props.stacked = Boolean(p.stacked);
				if ("max_points" in p) props.max_points = _cap(p.max_points);
				if ("x_format" in p) props.x_format = _fmt(p.x_format);
				const n = _strList(props.series, DEFAULTS.series).length;
				const cap = _cap(props.max_points);
				const cur = _points(props.value);
				if ("points" in p) {
					props.value = { points: _trim(_toPoints(p.points, n), cap) };
					return;
				}
				let pts = cur;
				if ("series" in p) pts = _reshape(pts, n);
				if (pts.length > cap) pts = _trim(pts, cap);
				if ("series" in p || pts !== cur) props.value = { points: pts };
			}),
		append: (ctx, payload) =>
			ctx.update((props) => {
				if (!Array.isArray(payload) || payload.length < 1) return;
				const n = _strList(props.series, DEFAULTS.series).length;
				if (n === 0) return;
				const pts = [..._points(props.value)];
				pts.push(_row(payload, n));
				props.value = { points: _trim(pts, _cap(props.max_points)) };
			}),
	},
};
