// LineChart -- display-only time-series chart.
//
// Server-owned. One `write` op carries every mutation (partial map);
// one `append` op pushes a single [x, y] point or a {name, x, y} row in
// multi-series mode. Class-level defaults (x_label, y_label, color,
// max_points, x_format, show_legend, show_tooltip, palette) ride in on
// the mount field `props` and seed the slice. Composes the kit LineChart
// primitive; the primitive owns chrome via chart-shared tokens.
//
// Single-series wire payload (legacy): {points: [[x, y], ...]}.
// Multi-series wire payload: {series: [{name, points: [[x, y], ...], color?}, ...]}.

import { LineChart as KitLineChart } from "../../components/ui/line-chart";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

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

function _pad2(n: number): string {
	return n < 10 ? `0${n}` : String(n);
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
			if ("x_label" in p) slice.x_label = p.x_label == null ? "" : String(p.x_label);
			if ("y_label" in p) slice.y_label = p.y_label == null ? "" : String(p.y_label);
			if ("color" in p) {
				if (typeof p.color === "string") slice.color = p.color;
			}
			if ("max_points" in p) slice.max_points = _cap(p.max_points);
			if ("x_format" in p) slice.x_format = _fmt(p.x_format);
			if ("show_legend" in p) slice.show_legend = Boolean(p.show_legend);
			if ("show_tooltip" in p) slice.show_tooltip = Boolean(p.show_tooltip);
			if ("palette" in p) slice.palette = _strList(p.palette);
			const cap = (slice.max_points as number) ?? DEFAULTS.max_points;
			if ("series" in p) {
				slice.value = { series: _trimSeries(_toSeries(p.series), cap) };
			} else if ("points" in p) {
				slice.value = { points: _trim(_toPoints(p.points), cap) };
			} else {
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
			const pts = Array.isArray(cur?.points) ? [...(cur?.points as Point[])] : [];
			if (Array.isArray(v) && v.length === 2) {
				pts.push([_num(v[0], pts.length), _y(v[1])]);
			}
			slice.value = { points: _trim(pts, cap) };
		}),
});

function LineChartView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value as LineChartValue | undefined);
	const color = useStore((s) => (s.refs[path]?.color as string) ?? DEFAULTS.color);
	const x_format = useStore((s) => (s.refs[path]?.x_format as XFormat) ?? "number");
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

export const LineChart: RefEntry = { factory, component: LineChartView };
