// LineChart -- display-only time-series chart.
//
// Server-owned. Chrome (x_label, y_label, color, max_points, x_format,
// show_legend, show_tooltip, palette) is plain props, declared at the slot
// and coerced where it is read. The data lives on `value`, either
// {points: [[x, y], ...]} in single-series mode or {series: [{name, points,
// color?}, ...]} in multi-series mode.
//
// Two handlers. `write` carries a partial map: which of `points` / `series`
// it names decides the mode, and both get trimmed to the current window, so
// the default merge cannot stand in for it. `append` pushes a single [x, y]
// point, or a {name, x, y} row onto one named series, and re-trims.
// Composes the kit LineChart primitive; the primitive owns chrome via
// chart-shared tokens.
//
// Single-series wire payload (legacy): {points: [[x, y], ...]}.
// Multi-series wire payload: {series: [{name, points: [[x, y], ...], color?}, ...]}.

import { LineChart as KitLineChart } from "../../components/ui/line-chart";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useProp,
	useStringProp,
	useValue,
} from "../../tree";

type Point = [number, number | null];
type Series = { name: string; points: Point[]; color?: string };
type LineChartValue = { points?: Point[]; series?: Series[] };
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
	color: "",
	max_points: 500,
	x_format: "number" as XFormat,
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

function _fmt(v: unknown): XFormat {
	return typeof v === "string" && (X_FORMATS as readonly string[]).includes(v)
		? (v as XFormat)
		: "number";
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
	else ms = v; // "time" and "datetime_ms" both treat v as ms
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

function _strList(v: unknown): string[] {
	if (!Array.isArray(v)) return [];
	return v.filter((e): e is string => typeof e === "string");
}

// A write payload that is not a map carries nothing this type understands.
function _map(v: unknown): Record<string, unknown> {
	return v != null && typeof v === "object" && !Array.isArray(v)
		? (v as Record<string, unknown>)
		: {};
}

function _value(v: unknown): LineChartValue | undefined {
	return v != null && typeof v === "object" && !Array.isArray(v)
		? (v as LineChartValue)
		: undefined;
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

function LineChartView({ path }: NodeProps) {
	const value = _value(useValue<unknown>(path, null));
	const color = useStringProp(path, "color", DEFAULTS.color);
	const x_format = _fmt(useProp<unknown>(path, "x_format", undefined));
	const show_legend = useBoolProp(path, "show_legend", DEFAULTS.show_legend);
	const show_tooltip = useBoolProp(path, "show_tooltip", DEFAULTS.show_tooltip);
	const palette = _strList(useProp<unknown>(path, "palette", undefined));

	const multi = Array.isArray(value?.series);
	const seriesList: Series[] = multi ? (value?.series as Series[]) : [];
	const singlePoints: Point[] = multi
		? []
		: Array.isArray(value?.points)
			? (value?.points as Point[])
			: [];

	const data: Record<string, number | string | null>[] = [];
	if (multi) {
		const byX = new Map<number, Record<string, number | string | null>>();
		for (let i = 0; i < seriesList.length; i++) {
			const s = seriesList[i];
			for (let k = 0; k < s.points.length; k++) {
				const p = s.points[k];
				const xNum = Array.isArray(p) ? _num(p[0], k) : k;
				const row = byX.get(xNum) ?? { x: _fmtTick(xNum, x_format) };
				row[s.name] = Array.isArray(p) ? _y(p[1]) : null;
				byX.set(xNum, row);
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
			const raw = Array.isArray(p) ? _num(p[0], i) : i;
			data.push({
				x: _fmtTick(raw, x_format),
				y: Array.isArray(p) ? _y(p[1]) : null,
			});
		}
	}

	const series = multi
		? seriesList.map((s, i) => {
				const c = s.color ?? palette[i];
				return c ? { dataKey: s.name, name: s.name, color: c } : { dataKey: s.name, name: s.name };
			})
		: color
			? [{ dataKey: "y", name: "value", color }]
			: [{ dataKey: "y", name: "value" }];

	return (
		<KitLineChart
			data={data}
			series={series}
			xKey="x"
			height={256}
			showLegend={multi && show_legend}
			showTooltip={show_tooltip}
		/>
	);
}

export const LineChart: NodeEntry = {
	component: LineChartView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				const p = _map(payload);
				if ("x_label" in p) props.x_label = p.x_label == null ? "" : String(p.x_label);
				if ("y_label" in p) props.y_label = p.y_label == null ? "" : String(p.y_label);
				if ("color" in p) {
					if (typeof p.color === "string") props.color = p.color;
				}
				if ("max_points" in p) props.max_points = _cap(p.max_points);
				if ("x_format" in p) props.x_format = _fmt(p.x_format);
				if ("show_legend" in p) props.show_legend = Boolean(p.show_legend);
				if ("show_tooltip" in p) props.show_tooltip = Boolean(p.show_tooltip);
				if ("palette" in p) props.palette = _strList(p.palette);
				const cap = _cap(props.max_points);
				if ("series" in p) {
					props.value = { series: _trimSeries(_toSeries(p.series), cap) };
					return;
				}
				if ("points" in p) {
					props.value = { points: _trim(_toPoints(p.points), cap) };
					return;
				}
				const cur = _value(props.value);
				if (cur?.series) {
					props.value = { series: _trimSeries(cur.series, cap) };
					return;
				}
				const pts = Array.isArray(cur?.points) ? (cur?.points as Point[]) : [];
				if (pts.length > cap) props.value = { points: _trim(pts, cap) };
			}),
		append: (ctx, payload) =>
			ctx.update((props) => {
				const cur = _value(props.value);
				const cap = _cap(props.max_points);
				if (
					payload &&
					typeof payload === "object" &&
					!Array.isArray(payload) &&
					"name" in payload
				) {
					const obj = payload as Record<string, unknown>;
					const name = typeof obj.name === "string" ? obj.name : "";
					if (!name) return;
					const curSeries = cur?.series;
					const list = Array.isArray(curSeries) ? [...curSeries] : [];
					const idx = list.findIndex((s) => s.name === name);
					const pt: Point = [_num(obj.x, 0), _y(obj.y)];
					if (idx === -1) {
						list.push({ name, points: [pt] });
					} else {
						const next = [...list[idx].points, pt];
						list[idx] = { ...list[idx], points: _trim(next, cap) };
					}
					props.value = { series: list.map((s) => ({ ...s, points: _trim(s.points, cap) })) };
					return;
				}
				const curPoints = cur?.points;
				const pts = Array.isArray(curPoints) ? [...curPoints] : [];
				if (Array.isArray(payload) && payload.length === 2) {
					pts.push([_num(payload[0], pts.length), _y(payload[1])]);
				}
				props.value = { points: _trim(pts, cap) };
			}),
	},
};
