// The sketch board's data: elements, palette, normalization and geometry.
// React-free, so the node's write handler and the tests share it with the
// component.
//
// A board's value is a list of elements. Every coordinate is normalized to
// 0..1 of the board, origin top-left, x across the width and y down the
// height. A `width` is the line width as a fraction of the board's shorter
// side, so a drawing reads the same at any pixel size.
//
//   {type: "path", points: [[x, y, pressure?], ...], stroke, width}
//   {type: "rect" | "ellipse", x, y, w, h, stroke, fill, width}
//   {type: "line" | "arrow", points: [[x1, y1], [x2, y2]], stroke, width}
//
// A color is a palette name (`ink`, `red`, `blue-soft`, ...) that resolves
// through kit roles, so it restains with the theme, or any CSS color (`#e11`)
// drawn as is. `none` is no fill.

import { getStroke } from "perfect-freehand";

export type SketchTool = "pen" | "rect" | "ellipse" | "line" | "arrow";
export type SketchShape = Exclude<SketchTool, "pen">;
export type SketchControl = "tools" | "stroke" | "fill" | "size" | "undo" | "redo" | "clear";

export const SKETCH_TOOLS: readonly SketchTool[] = ["pen", "rect", "ellipse", "line", "arrow"];
export const SKETCH_SHAPES: readonly SketchShape[] = ["rect", "ellipse", "line", "arrow"];
export const SKETCH_CONTROLS: readonly SketchControl[] = [
	"tools",
	"stroke",
	"fill",
	"size",
	"undo",
	"redo",
	"clear",
];

/** A point: [x, y] or, from a pen, [x, y, pressure]. */
export type SketchPoint = [number, number] | [number, number, number];

export type SketchPath = { type: "path"; points: SketchPoint[]; stroke: string; width: number };
export type SketchBox = {
	type: "rect" | "ellipse";
	x: number;
	y: number;
	w: number;
	h: number;
	stroke: string;
	fill: string;
	width: number;
};
export type SketchLine = {
	type: "line" | "arrow";
	points: [[number, number], [number, number]];
	stroke: string;
	width: number;
};
export type SketchElement = SketchPath | SketchBox | SketchLine;

export type SketchDefaults = { tool: SketchTool; stroke: string; fill: string; size: number };

export const SKETCH_DEFAULTS: SketchDefaults = {
	tool: "pen",
	stroke: "ink",
	fill: "none",
	size: 0.012,
};

// --- palette ------------------------------------------------------------------

/** Stroke colors the toolbar offers, in order. */
export const SKETCH_STROKES = ["ink", "gray", "red", "amber", "green", "blue", "violet"] as const;
/** Fill colors the toolbar offers, in order. */
export const SKETCH_FILLS = [
	"none",
	"gray-soft",
	"red-soft",
	"amber-soft",
	"green-soft",
	"blue-soft",
	"violet-soft",
] as const;
/** Line widths the toolbar offers, as fractions of the shorter side. */
export const SKETCH_SIZES = [0.006, 0.012, 0.024, 0.048] as const;

// Kit roles only, never a hex: the board restains with the theme for free.
const PALETTE: Record<string, string> = {
	ink: "var(--text-primary)",
	gray: "var(--text-muted)",
	red: "var(--status-danger)",
	amber: "var(--status-warn)",
	green: "var(--status-ok)",
	blue: "var(--accent-2)",
	violet: "var(--accent)",
	"gray-soft": "var(--bg-press)",
	"red-soft": "var(--status-danger-wash)",
	"amber-soft": "var(--status-warn-wash)",
	"green-soft": "var(--status-ok-wash)",
	"blue-soft": "var(--accent-2-soft)",
	"violet-soft": "var(--accent-soft)",
};

/** A color name or CSS color as an SVG paint value. */
export function sketchColor(color: string): string {
	if (color === "none" || color === "") return "none";
	return PALETTE[color] ?? color;
}

// --- normalization ----------------------------------------------------------------

const clamp01 = (n: number) => (n < 0 ? 0 : n > 1 ? 1 : n);
const num = (v: unknown): number | null => {
	const n = typeof v === "number" ? v : typeof v === "string" && v.trim() !== "" ? Number(v) : NaN;
	return Number.isFinite(n) ? n : null;
};
const colorOr = (v: unknown, fallback: string) =>
	typeof v === "string" && v.trim() !== "" ? v.trim() : fallback;
const widthOr = (v: unknown, fallback: number) => {
	const n = num(v);
	return n !== null && n > 0 ? Math.min(n, 1) : fallback;
};

function point(raw: unknown, withPressure: boolean): SketchPoint | null {
	if (!Array.isArray(raw) || raw.length < 2) return null;
	const x = num(raw[0]);
	const y = num(raw[1]);
	if (x === null || y === null) return null;
	const p = withPressure && raw.length > 2 ? num(raw[2]) : null;
	return p === null ? [clamp01(x), clamp01(y)] : [clamp01(x), clamp01(y), clamp01(p)];
}

function points(raw: unknown, withPressure: boolean): SketchPoint[] {
	if (!Array.isArray(raw)) return [];
	const out: SketchPoint[] = [];
	for (const p of raw) {
		const pt = point(p, withPressure);
		if (pt) out.push(pt);
	}
	return out;
}

/** One element off the wire, or null when there is nothing drawable in it. */
export function normalizeElement(
	raw: unknown,
	defaults: Pick<SketchDefaults, "stroke" | "fill" | "size"> = SKETCH_DEFAULTS,
): SketchElement | null {
	// A bare list of points is a pen stroke: the first sketch pad's value.
	if (Array.isArray(raw)) raw = { type: "path", points: raw };
	if (!raw || typeof raw !== "object") return null;
	const el = raw as Record<string, unknown>;
	const stroke = colorOr(el.stroke, defaults.stroke);
	const width = widthOr(el.width, defaults.size);
	switch (el.type) {
		case "path": {
			const pts = points(el.points, true);
			return pts.length ? { type: "path", points: pts, stroke, width } : null;
		}
		case "rect":
		case "ellipse": {
			let x = num(el.x);
			let y = num(el.y);
			let w = num(el.w);
			let h = num(el.h);
			if (x === null || y === null || w === null || h === null) return null;
			if (w < 0) [x, w] = [x + w, -w];
			if (h < 0) [y, h] = [y + h, -h];
			x = clamp01(x);
			y = clamp01(y);
			w = Math.min(w, 1 - x);
			h = Math.min(h, 1 - y);
			if (w <= 0 && h <= 0) return null;
			return { type: el.type, x, y, w, h, stroke, fill: colorOr(el.fill, defaults.fill), width };
		}
		case "line":
		case "arrow": {
			const pts = points(el.points, false);
			if (pts.length < 2) return null;
			const a: [number, number] = [pts[0][0], pts[0][1]];
			const b: [number, number] = [pts[pts.length - 1][0], pts[pts.length - 1][1]];
			return { type: el.type, points: [a, b], stroke, width };
		}
		default:
			return null;
	}
}

/** Wire value -> elements. Anything off-shape is dropped, never thrown on. */
export function normalizeElements(
	raw: unknown,
	defaults: Pick<SketchDefaults, "stroke" | "fill" | "size"> = SKETCH_DEFAULTS,
): SketchElement[] {
	if (!Array.isArray(raw)) return [];
	const out: SketchElement[] = [];
	for (const item of raw) {
		const el = normalizeElement(item, defaults);
		if (el) out.push(el);
	}
	return out;
}

/** Board config off the wire: known tools and controls only, defaults filled in. */
export function sketchConfig(raw: { tools?: unknown; controls?: unknown; defaults?: unknown }): {
	tools: SketchTool[];
	controls: SketchControl[];
	defaults: SketchDefaults;
} {
	const pick = <T extends string>(v: unknown, all: readonly T[]): T[] =>
		Array.isArray(v) ? all.filter((t) => v.includes(t)) : [...all];
	const tools = pick(raw.tools, SKETCH_TOOLS);
	const usable = tools.length ? tools : (["pen"] as SketchTool[]);
	const controls = pick(raw.controls, SKETCH_CONTROLS);
	const d = (raw.defaults && typeof raw.defaults === "object" ? raw.defaults : {}) as Record<
		string,
		unknown
	>;
	const tool = usable.includes(d.tool as SketchTool) ? (d.tool as SketchTool) : usable[0];
	return {
		tools: usable,
		controls,
		defaults: {
			tool,
			stroke: colorOr(d.stroke, SKETCH_DEFAULTS.stroke),
			fill: colorOr(d.fill, SKETCH_DEFAULTS.fill),
			size: widthOr(d.size, SKETCH_DEFAULTS.size),
		},
	};
}

// --- geometry ---------------------------------------------------------------------

const r2 = (n: number) => Math.round(n * 100) / 100;

/** perfect-freehand's outline polygon as SVG path data, midpoint quadratics. */
function outlinePath(outline: number[][]): string {
	const n = outline.length;
	if (n < 3) return "";
	let d = `M${r2(outline[0][0])} ${r2(outline[0][1])}Q`;
	for (let i = 0; i < n; i++) {
		const [x0, y0] = outline[i];
		const [x1, y1] = outline[(i + 1) % n];
		d += `${r2(x0)} ${r2(y0)} ${r2((x0 + x1) / 2)} ${r2((y0 + y1) / 2)} `;
	}
	return `${d}Z`;
}

/**
 * Pen ink as a filled outline, in board pixels. Pressure from a pen when the
 * points carry it, simulated from speed otherwise. `last` is false while the
 * stroke is still in flight, so its tail does not taper under the pointer.
 */
export function freehandPath(
	pts: SketchPoint[],
	sizePx: number,
	boardW: number,
	boardH: number,
	last = true,
): string {
	const pressured = pts.some((p) => p.length > 2);
	const px = pts.map((p) => [p[0] * boardW, p[1] * boardH, p[2] ?? 0.5]);
	const outline = getStroke(px, {
		size: sizePx,
		thinning: 0.5,
		smoothing: 0.5,
		streamline: 0.45,
		simulatePressure: !pressured,
		last,
	});
	return outlinePath(outline);
}

/** An arrow's shaft and head as one open path, in board pixels. */
export function arrowPath(
	[x1, y1]: [number, number],
	[x2, y2]: [number, number],
	widthPx: number,
): string {
	const len = Math.hypot(x2 - x1, y2 - y1);
	if (len === 0) return `M${x1} ${y1}L${x2} ${y2}`;
	const head = Math.min(Math.max(widthPx * 4, 10), len * 0.6);
	const a = Math.atan2(y2 - y1, x2 - x1);
	const spread = Math.PI / 7;
	const hx1 = x2 - head * Math.cos(a - spread);
	const hy1 = y2 - head * Math.sin(a - spread);
	const hx2 = x2 - head * Math.cos(a + spread);
	const hy2 = y2 - head * Math.sin(a + spread);
	return `M${r2(x1)} ${r2(y1)}L${r2(x2)} ${r2(y2)}M${r2(hx1)} ${r2(hy1)}L${r2(x2)} ${r2(y2)}L${r2(hx2)} ${r2(hy2)}`;
}
