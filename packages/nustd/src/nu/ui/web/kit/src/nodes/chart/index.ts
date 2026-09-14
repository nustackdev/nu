// Chart node types: output sinks with chart-shaped payloads.

import type { NodeEntry } from "../../tree";
import { AreaChart } from "./area-chart";
import { BarChart } from "./bar-chart";
import { LineChart } from "./line-chart";
import { PieChart } from "./pie-chart";
import { Sparkline } from "./sparkline";

export const chartEntries: Record<string, NodeEntry> = {
	LineChart,
	AreaChart,
	BarChart,
	PieChart,
	Sparkline,
};
