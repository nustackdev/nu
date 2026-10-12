// ECharts, loaded the first time a chart mounts.
//
// Two builds. The modular one (./modular) carries the typed charts; the full
// one carries everything else a raw option may ask for (geo maps, polar,
// dataZoom, ...). Both are dynamic imports, so neither lands in an app's
// main chunk, and each loads at most once per page.

import type * as Core from "echarts/core";

export type ECharts = typeof Core;
export type EChartsInstance = Core.EChartsType;

let modular: Promise<ECharts> | null = null;
let full: Promise<ECharts> | null = null;
const loaded: ECharts[] = [];
const maps = new Map<string, [object, object | undefined]>();

function adopt(lib: ECharts): ECharts {
	for (const [name, [geo, areas]] of maps) lib.registerMap(name, geo as never, areas as never);
	loaded.push(lib);
	return lib;
}

/** The build an option needs. `full` for anything outside the typed set. */
export function loadECharts(wantFull: boolean): Promise<ECharts> {
	if (wantFull) {
		full ??= import("echarts").then((m) => adopt(m as unknown as ECharts));
		return full;
	}
	modular ??= import("./modular").then((m) => adopt(m.default as unknown as ECharts));
	return modular;
}

/**
 * Register a GeoJSON map under `name`, for an option with a `geo` component or
 * a `map` series to draw by that name. Safe to call before any chart loads:
 * the map is handed to each build as it arrives.
 */
export function registerChartMap(name: string, geoJSON: object, specialAreas?: object): void {
	maps.set(name, [geoJSON, specialAreas]);
	for (const lib of loaded) lib.registerMap(name, geoJSON as never, specialAreas as never);
}
