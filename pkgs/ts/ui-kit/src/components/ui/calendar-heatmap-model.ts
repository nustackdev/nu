// Calendar heatmap model: pure date math, levels and labels, no React.
//
// A day's value is a number, or a record of named parts ({jobs: 2, builds:
// 7}) whose sum is the shade. Days are keyed by local `YYYY-MM-DD`. The grid
// is `weeks` columns of 7 rows, ending with the week that holds `end`; days
// after `end` are padding and carry no value.

export type CalendarHeatmapValue = number | Record<string, number>;
export type CalendarHeatmapValues = Record<string, CalendarHeatmapValue>;
export type CalendarHeatmapWeekStart = "mon" | "sun";

/** 0 is an empty day, 1..4 the quartile steps. `null` is a padding square. */
export type CalendarHeatmapLevel = 0 | 1 | 2 | 3 | 4;

export interface CalendarHeatmapDay {
	key: string;
	date: Date;
	/** Parts as given; a plain number becomes one unnamed part. */
	parts: [string, number][];
	total: number;
	/** null past `end`: drawn as nothing, no tooltip. */
	level: CalendarHeatmapLevel | null;
}

export interface CalendarHeatmapMonth {
	week: number;
	label: string;
}

export interface CalendarHeatmapModel {
	days: CalendarHeatmapDay[];
	months: CalendarHeatmapMonth[];
	/** Sum per part over the window, in first-seen order. */
	totals: [string, number][];
	peak: CalendarHeatmapDay | null;
}

export const MONTHS = [
	"Jan",
	"Feb",
	"Mar",
	"Apr",
	"May",
	"Jun",
	"Jul",
	"Aug",
	"Sep",
	"Oct",
	"Nov",
	"Dec",
] as const;

const pad = (n: number) => String(n).padStart(2, "0");

export function dayKey(d: Date): string {
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** `YYYY-MM-DD` as a local date; anything else is null. */
export function parseDay(s: string): Date | null {
	const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
	if (!m) return null;
	const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
	return Number.isNaN(d.getTime()) ? null : d;
}

function num(v: unknown): number {
	return typeof v === "number" && Number.isFinite(v) && v > 0 ? v : 0;
}

export function partsOf(v: CalendarHeatmapValue | undefined): [string, number][] {
	if (v == null) return [];
	if (typeof v === "number") return [["", num(v)]];
	if (typeof v !== "object") return [];
	return Object.entries(v).map(([k, n]) => [k, num(n)]);
}

/** Quartile cut points over the non-zero totals, as the levels 1..3 ceilings. */
export function thresholds(totals: number[]): [number, number, number] {
	const vals = totals.filter((v) => v > 0).sort((a, b) => a - b);
	const q = (p: number) => vals[Math.floor(p * (vals.length - 1))] ?? 0;
	return [q(0.25), q(0.5), q(0.75)];
}

export function levelOf(total: number, th: [number, number, number]): CalendarHeatmapLevel {
	if (total <= 0) return 0;
	if (total <= th[0]) return 1;
	if (total <= th[1]) return 2;
	if (total <= th[2]) return 3;
	return 4;
}

export function buildModel(
	values: CalendarHeatmapValues,
	end: Date,
	weeks: number,
	weekStart: CalendarHeatmapWeekStart,
): CalendarHeatmapModel {
	const last = new Date(end.getFullYear(), end.getMonth(), end.getDate());
	const offset = weekStart === "mon" ? (last.getDay() + 6) % 7 : last.getDay();
	const y = last.getFullYear();
	const m = last.getMonth();
	const first = last.getDate() - offset - (weeks - 1) * 7;

	const days: CalendarHeatmapDay[] = [];
	const totals = new Map<string, number>();
	for (let i = 0; i < weeks * 7; i++) {
		const date = new Date(y, m, first + i);
		const key = dayKey(date);
		const inside = date <= last;
		const parts = inside ? partsOf(values[key]) : [];
		const total = parts.reduce((s, [, n]) => s + n, 0);
		for (const [k, n] of parts) totals.set(k, (totals.get(k) ?? 0) + n);
		days.push({ key, date, parts, total, level: inside ? 0 : null });
	}

	const th = thresholds(days.map((d) => d.total));
	let peak: CalendarHeatmapDay | null = null;
	for (const d of days) {
		if (d.level === null) continue;
		d.level = levelOf(d.total, th);
		if (d.total > 0 && (!peak || d.total > peak.total)) peak = d;
	}

	const months: CalendarHeatmapMonth[] = [];
	for (let w = 1; w < weeks; w++) {
		const d = days[w * 7].date;
		if (d.getDate() <= 7) months.push({ week: w, label: MONTHS[d.getMonth()] });
	}

	return { days, months, totals: [...totals], peak };
}

const fullFmt = new Intl.NumberFormat("en-US");
const compactFmt = new Intl.NumberFormat("en-US", {
	notation: "compact",
	maximumFractionDigits: 1,
});

/** Full below 1,000, compact from there so tooltips stay short. */
export function formatCount(n: number): string {
	return n >= 1000 ? compactFmt.format(n) : fullFmt.format(n);
}

export function formatFull(n: number): string {
	return fullFmt.format(n);
}

/** A part key is a plural noun; one of it drops the trailing s. */
export function noun(key: string, n: number): string {
	return n === 1 && key.endsWith("s") ? key.slice(0, -1) : key;
}

/** "2 jobs, 7 builds", or "12 commits" for a plain value with a unit. */
export function describeParts(
	parts: [string, number][],
	unit = "",
	format: (n: number) => string = formatCount,
): string {
	return parts
		.map(([k, n]) => {
			const name = noun(k || unit, n);
			return name ? `${format(n)} ${name}` : format(n);
		})
		.join(", ");
}

export function formatDay(d: Date): string {
	return `${MONTHS[d.getMonth()]} ${d.getDate()}`;
}

/** Tooltip line: "Nov 10: 2 jobs, 7 builds finished", "Nov 9: nothing finished". */
export function describeDay(day: CalendarHeatmapDay, unit = "", suffix = ""): string {
	const tail = suffix ? ` ${suffix}` : "";
	const body = day.total > 0 ? describeParts(day.parts, unit) : "nothing";
	return `${formatDay(day.date)}: ${body}${tail}`;
}
