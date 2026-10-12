// Kitchen sink: every typed chart, drawn by the one Chart primitive from the
// option its Python builder makes, light and dark side by side. The kit
// Gauge (not an ECharts chart) closes the page.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { Chart } from "../../components/ui/chart";
import { Gauge } from "../../components/ui/gauge";
import { type SampleName, sample, sampleOption } from "../refs/chart-samples";
import { Block, Row, SinkPage, sinkParameters, ThemePair } from "./frame";

const GAUGE_TONES = ["accent", "accent2", "info", "ok", "warn", "danger"] as const;

// Row label (the Python builder and what it is set to) to sample.
const ROWS: [string, SampleName[]][] = [
	["LineChart", ["line", "line-time"]],
	["AreaChart stack", ["area-stacked"]],
	["BarChart", ["bar", "bar-stacked"]],
	["BarChart horizontal", ["bar-horizontal"]],
	["ScatterChart", ["scatter"]],
	["Histogram", ["histogram"]],
	["BoxplotChart", ["boxplot"]],
	["CandlestickChart", ["candlestick"]],
	["HeatmapChart", ["heatmap"]],
	["PieChart", ["pie", "donut"]],
	["FunnelChart", ["funnel"]],
	["RadarChart", ["radar"]],
	["TreemapChart", ["treemap"]],
	["SunburstChart", ["sunburst"]],
	["SankeyChart", ["sankey"]],
	["GaugeChart", ["gauge"]],
];

function Charts() {
	return (
		<Block title="Charts">
			{ROWS.map(([label, names]) => (
				<Row key={label} label={label} className="grid grid-cols-1 gap-4 xl:grid-cols-2">
					{names.map((name) => (
						<Chart
							key={name}
							option={sampleOption(name)}
							height={sample(name).props.height ?? 256}
						/>
					))}
				</Row>
			))}
			<Row label="Sparkline">
				{[0, 1, 2, 3].map((i) => (
					<div key={i} className="w-28">
						<Chart
							option={{ ...sampleOption("sparkline"), color: [`var(--chart-${i + 1})`] }}
							height={28}
						/>
					</div>
				))}
			</Row>
			<Row label="Gauge (kit)">
				{GAUGE_TONES.map((tone, i) => (
					<Gauge key={tone} size="sm" tone={tone} value={30 + i * 12} label={tone} />
				))}
				<Gauge size="md" value={72} label="CPU" />
				<Gauge size="lg" value={41} label="Memory" />
			</Row>
		</Block>
	);
}

export const Default: StoryObj = {
	name: "Charts",
	render: () => (
		<SinkPage
			title="Charts"
			description="Every typed chart: one ECharts primitive, the option from its Python builder."
		>
			<ThemePair>
				<Charts />
			</ThemePair>
		</SinkPage>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Charts",
	parameters: sinkParameters,
};

export default meta;
