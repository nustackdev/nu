// Chart node types. One: `Chart`, an ECharts option. The typed charts
// (line, bar, pie, ...) are Python builders over it, not node types.

import type { NodeEntry } from "../../tree";
import { ChartNode } from "./chart";

export const chartEntries: Record<string, NodeEntry> = {
	Chart: ChartNode,
};
