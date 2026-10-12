// The modular ECharts build: the core plus only what the typed charts draw.
//
// Loaded on demand by ./load, never imported statically, so a page with no
// chart never fetches it. The set matches MODULAR_SERIES in ./option; an
// option reaching past it gets the full build instead.

import {
	BarChart,
	BoxplotChart,
	CandlestickChart,
	FunnelChart,
	GaugeChart,
	HeatmapChart,
	LineChart,
	PieChart,
	RadarChart,
	SankeyChart,
	ScatterChart,
	SunburstChart,
	TreemapChart,
} from "echarts/charts";
import {
	AriaComponent,
	DatasetComponent,
	GridComponent,
	LegendComponent,
	MarkLineComponent,
	RadarComponent,
	TitleComponent,
	TooltipComponent,
	VisualMapComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { LabelLayout, UniversalTransition } from "echarts/features";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
	BarChart,
	BoxplotChart,
	CandlestickChart,
	FunnelChart,
	GaugeChart,
	HeatmapChart,
	LineChart,
	PieChart,
	RadarChart,
	SankeyChart,
	ScatterChart,
	SunburstChart,
	TreemapChart,
	AriaComponent,
	DatasetComponent,
	GridComponent,
	LegendComponent,
	MarkLineComponent,
	RadarComponent,
	TitleComponent,
	TooltipComponent,
	VisualMapComponent,
	LabelLayout,
	UniversalTransition,
	CanvasRenderer,
]);

export default echarts;
