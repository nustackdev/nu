// ECharts option helpers that need no ECharts: merge, series lookup, and
// which build an option needs.
//
// The node keeps the option it was given as plain data in the store, and a
// `merge` from the server has to land there the way ECharts would apply it,
// so a remount (or a theme switch, which re-inits) redraws the same chart.
// `mergeOption` is that: pure, structurally shared, ECharts' rules.

export type ChartOption = Record<string, unknown>;
type Item = Record<string, unknown>;

export function isPlain(v: unknown): v is Item {
	return typeof v === "object" && v !== null && !Array.isArray(v);
}

// An array is merged item by item only when it holds components (objects).
// `color: [...]` or `data: [...]` are values, and a value is replaced whole.
function isComponentList(v: unknown): v is unknown[] {
	return Array.isArray(v) && v.length > 0 && v.every(isPlain);
}

// Where each patch item lands in `list`, ECharts' three passes: same id, then
// same name, then the first slot nothing has claimed yet. An item with an id
// that matches nothing, or one with no free slot left, goes on the end
// (-1). Lands are distinct.
function placements(list: unknown[], patch: Item[]): number[] {
	const at = patch.map(() => -1);
	const taken = new Set<number>();
	const claim = (k: number, i: number) => {
		at[k] = i;
		taken.add(i);
	};
	patch.forEach((item, k) => {
		if (item.id == null) return;
		const i = list.findIndex((e, n) => !taken.has(n) && isPlain(e) && e.id === item.id);
		if (i >= 0) claim(k, i);
	});
	patch.forEach((item, k) => {
		if (at[k] >= 0 || item.id != null || item.name == null) return;
		const i = list.findIndex((e, n) => !taken.has(n) && isPlain(e) && e.name === item.name);
		if (i >= 0) claim(k, i);
	});
	patch.forEach((item, k) => {
		if (at[k] >= 0 || item.id != null) return;
		const i = list.findIndex((_, n) => !taken.has(n));
		if (i >= 0) claim(k, i);
	});
	return at;
}

function mergeValue(base: unknown, patch: unknown): unknown {
	if (patch === undefined) return base;
	if (isPlain(base) && isPlain(patch)) return mergeObject(base, patch);
	return patch;
}

function mergeObject(base: Item, patch: Item): Item {
	const out: Item = { ...base };
	for (const [k, v] of Object.entries(patch)) out[k] = mergeValue(base[k], v);
	return out;
}

/** Merge a list of components: each patch item onto its match, the rest appended. */
export function mergeList(base: unknown[], patch: Item[]): unknown[] {
	const out = [...base];
	placements(base, patch).forEach((at, k) => {
		if (at >= 0) out[at] = mergeValue(out[at], patch[k]);
		else out.push(patch[k]);
	});
	return out;
}

/** `patch` applied to `base` with ECharts setOption merge semantics. Neither is mutated. */
export function mergeOption(base: ChartOption, patch: ChartOption): ChartOption {
	const out: ChartOption = { ...base };
	for (const [key, value] of Object.entries(patch)) {
		const cur = base[key];
		// A component given as one object on one side and a list on the
		// other is still the same component list (`xAxis: {...}` is
		// `xAxis: [{...}]` to ECharts).
		const curList = isComponentList(cur) ? cur : isPlain(cur) ? [cur] : null;
		const patchList = isComponentList(value) ? value : null;
		if (patchList && curList) {
			out[key] = mergeList(curList, patchList as Item[]);
		} else if (isPlain(value) && Array.isArray(cur) && isComponentList(cur)) {
			out[key] = mergeList(cur, [value]);
		} else {
			out[key] = mergeValue(cur, value);
		}
	}
	return out;
}

/** The option's series as a list, however it was spelled. */
export function seriesOf(option: ChartOption): Item[] {
	const s = option.series;
	if (Array.isArray(s)) return s.filter(isPlain);
	return isPlain(s) ? [s] : [];
}

/** Index of the series a key names: a position, an id, or a name. -1 when none. */
export function findSeries(option: ChartOption, key: unknown): number {
	const list = seriesOf(option);
	if (typeof key === "number")
		return Number.isInteger(key) && key >= 0 && key < list.length ? key : -1;
	if (typeof key !== "string") return -1;
	const byId = list.findIndex((s) => s.id === key);
	return byId >= 0 ? byId : list.findIndex((s) => s.name === key);
}

/** Which series a merge patch hands new `data` to, as indexes into the merged option. */
export function seriesWithData(base: ChartOption, patch: ChartOption): number[] {
	const raw = patch.series;
	const items = Array.isArray(raw) ? raw.filter(isPlain) : isPlain(raw) ? [raw] : [];
	const list = seriesOf(base);
	let next = list.length;
	const out: number[] = [];
	placements(list, items).forEach((at, k) => {
		const index = at >= 0 ? at : next++;
		if ("data" in items[k]) out.push(index);
	});
	return out;
}

/** The option with some series' `data` swapped for what a stream holds. */
export function withSeriesData(option: ChartOption, data: Map<number, unknown[]>): ChartOption {
	if (data.size === 0) return option;
	const list = seriesOf(option).map((s, i) => (data.has(i) ? { ...s, data: data.get(i) } : s));
	return { ...option, series: list };
}

// What the modular build registers. An option that reaches past it (a geo
// map, a polar axis, a dataZoom) loads the full build instead.
export const MODULAR_SERIES = new Set([
	"line",
	"bar",
	"pie",
	"scatter",
	"heatmap",
	"radar",
	"treemap",
	"sunburst",
	"sankey",
	"funnel",
	"gauge",
	"boxplot",
	"candlestick",
]);

const FULL_ONLY_COMPONENTS = [
	"geo",
	"polar",
	"angleAxis",
	"radiusAxis",
	"parallel",
	"parallelAxis",
	"singleAxis",
	"calendar",
	"dataZoom",
	"brush",
	"toolbox",
	"timeline",
	"graphic",
	"matrix",
	"thumbnail",
];

const FULL_ONLY_SERIES_PARTS = ["markPoint", "markArea"];

/** Whether drawing this option takes the full ECharts build. */
export function needsFull(option: ChartOption): boolean {
	for (const key of FULL_ONLY_COMPONENTS) if (option[key] != null) return true;
	for (const s of seriesOf(option)) {
		const type = typeof s.type === "string" ? s.type : "line";
		if (!MODULAR_SERIES.has(type)) return true;
		for (const part of FULL_ONLY_SERIES_PARTS) if (s[part] != null) return true;
	}
	return false;
}
