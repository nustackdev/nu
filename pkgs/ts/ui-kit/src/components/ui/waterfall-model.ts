// Waterfall model: pure data work behind the Waterfall primitive.
//
// Spans arrive as a flat list with an optional `parent` id. `waterfallRows`
// lays them out as a trace view reads them: roots by start time, each
// followed by its children by start time, depth first. A span whose parent
// is not in the list is a root. A span caught in a parent cycle is never
// reached from a root, so it is added as a root at the end: no span is
// dropped. Past `maxRows` the rest are counted, not drawn, with their problem
// spans (danger) counted apart, since a time-ordered list cannot move a
// failure above the cap the way StatusSquares does.
//
// Times are plain numbers in milliseconds, epoch or relative. The axis reads
// offsets from the window start, so either works.

export const WATERFALL_TONES = ["neutral", "info", "ok", "warn", "danger"] as const;

export type WaterfallTone = (typeof WATERFALL_TONES)[number];

export interface WaterfallSpan {
	id: string;
	label: string;
	/** Start, in ms. */
	start: number;
	/** End, in ms. Missing or null: still running, drawn to `now`. */
	end?: number | null;
	tone?: WaterfallTone;
	/** Id of the span this one runs inside. Missing: a root. */
	parent?: string | null;
	/** One more line for the hover hint. */
	detail?: string;
}

export interface WaterfallRow {
	span: WaterfallSpan;
	depth: number;
}

export interface WaterfallLayout {
	rows: WaterfallRow[];
	/** Spans past the cap, counted, not drawn. */
	hidden: number;
	/** Of the hidden ones, how many are danger. */
	hiddenDanger: number;
}

export function isTone(v: unknown): v is WaterfallTone {
	return typeof v === "string" && (WATERFALL_TONES as readonly string[]).includes(v);
}

export function toneOf(span: WaterfallSpan): WaterfallTone {
	return isTone(span.tone) ? span.tone : "neutral";
}

export function isRunning(span: WaterfallSpan): boolean {
	return span.end == null || !Number.isFinite(span.end);
}

/** Every span in trace order, then capped to `maxRows`. */
export function waterfallRows(
	spans: readonly WaterfallSpan[],
	maxRows = Infinity,
): WaterfallLayout {
	const ids = new Set(spans.map((s) => s.id));
	const kids = new Map<string, WaterfallSpan[]>();
	const roots: WaterfallSpan[] = [];
	for (const s of spans) {
		const p = s.parent;
		if (p != null && p !== s.id && ids.has(p)) {
			const list = kids.get(p);
			if (list) list.push(s);
			else kids.set(p, [s]);
		} else roots.push(s);
	}
	const byStart = (a: WaterfallSpan, b: WaterfallSpan) => a.start - b.start;
	const all: WaterfallRow[] = [];
	const seen = new Set<WaterfallSpan>();
	const walk = (s: WaterfallSpan, depth: number) => {
		if (seen.has(s)) return;
		seen.add(s);
		all.push({ span: s, depth });
		for (const k of [...(kids.get(s.id) ?? [])].sort(byStart)) walk(k, depth + 1);
	};
	for (const r of [...roots].sort(byStart)) walk(r, 0);
	// A parent cycle is unreachable from any root; draw it flat, never drop it.
	for (const s of spans) if (!seen.has(s)) walk(s, 0);

	const cap = Math.max(0, Math.floor(maxRows));
	const rows = all.slice(0, cap);
	const rest = all.slice(cap);
	return {
		rows,
		hidden: rest.length,
		hiddenDanger: rest.filter((r) => toneOf(r.span) === "danger").length,
	};
}

/** The time window: earliest start to latest end (or `now` for running spans). */
export function waterfallWindow(
	spans: readonly WaterfallSpan[],
	opts: { start?: number; end?: number; now?: number } = {},
): { start: number; end: number } {
	let lo = Infinity;
	let hi = -Infinity;
	for (const s of spans) {
		if (!Number.isFinite(s.start)) continue;
		lo = Math.min(lo, s.start);
		hi = Math.max(hi, isRunning(s) ? (opts.now ?? s.start) : (s.end as number), s.start);
	}
	if (opts.now != null && spans.some(isRunning)) hi = Math.max(hi, opts.now);
	const start = opts.start ?? (Number.isFinite(lo) ? lo : 0);
	let end = opts.end ?? (Number.isFinite(hi) ? hi : start);
	if (end <= start) end = start + 1;
	return { start, end };
}

/** Where a running span stops: `now` when given, else the window end. */
export function spanEnd(span: WaterfallSpan, windowEnd: number, now?: number): number {
	return isRunning(span) ? (now ?? windowEnd) : (span.end as number);
}

/** Axis ticks as offsets from the window start, on a 1/2/5 step, about `target` of them. */
export function waterfallTicks(range: number, target = 5): number[] {
	if (!(range > 0)) return [0];
	const raw = range / target;
	const mag = 10 ** Math.floor(Math.log10(raw));
	const step = [1, 2, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? 10 * mag;
	const out: number[] = [];
	for (let t = 0; t <= range + step * 1e-9; t += step) out.push(Math.round(t / step) * step);
	return out;
}

/** A duration or offset in ms, short: 0 ms, 8.5 ms, 120 ms, 1.25 s, 42.1 s, 3m 05s, 1h 02m. */
export function formatSpanTime(ms: number): string {
	if (!Number.isFinite(ms)) return "";
	const a = Math.abs(ms);
	const sign = ms < 0 ? "-" : "";
	if (a < 10) return `${sign}${trim(a.toFixed(1))} ms`;
	if (a < 1000) return `${sign}${Math.round(a)} ms`;
	if (a < 10_000) return `${sign}${trim((a / 1000).toFixed(2))} s`;
	if (a < 60_000) return `${sign}${trim((a / 1000).toFixed(1))} s`;
	if (a < 3_600_000) {
		const m = Math.floor(a / 60_000);
		const s = Math.floor((a % 60_000) / 1000);
		return `${sign}${m}m ${String(s).padStart(2, "0")}s`;
	}
	const h = Math.floor(a / 3_600_000);
	const m = Math.floor((a % 3_600_000) / 60_000);
	return `${sign}${h}h ${String(m).padStart(2, "0")}m`;
}

function trim(s: string): string {
	return s.includes(".") ? s.replace(/\.?0+$/, "") : s;
}
