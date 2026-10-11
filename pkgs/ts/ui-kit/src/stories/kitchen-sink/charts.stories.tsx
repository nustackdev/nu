// Kitchen sink: every chart, all 8 categorical slots where a chart takes
// several series, light and dark side by side.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { AreaChart } from "../../components/ui/area-chart";
import { BarChart } from "../../components/ui/bar-chart";
import { CHART_PALETTE_SIZE, chartColor } from "../../components/ui/chart-shared";
import { Gauge } from "../../components/ui/gauge";
import { LineChart } from "../../components/ui/line-chart";
import { PieChart } from "../../components/ui/pie-chart";
import { Sparkline } from "../../components/ui/sparkline";
import { Block, Row, SinkPage, ThemePair, sinkParameters } from "./frame";

const SLOTS = Array.from({ length: CHART_PALETTE_SIZE }, (_, i) => i);
const SERIES = SLOTS.map((i) => ({ dataKey: `s${i + 1}`, name: `Series ${i + 1}` }));
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];

// Deterministic wiggle per series so each line is told apart.
const DATA = MONTHS.map((month, m) => {
	const row: Record<string, unknown> = { month };
	for (const i of SLOTS) row[`s${i + 1}`] = 10 + i * 4 + ((m * (i + 3)) % 9);
	return row;
});

const PIE = SLOTS.map((i) => ({ name: `Slot ${i + 1}`, value: 8 + ((i * 5) % 11) }));
const SPARK = [4, 7, 5, 9, 6, 11, 8, 12, 10, 14];
const GAUGE_TONES = ["accent", "accent2", "info", "ok", "warn", "danger"] as const;

function Charts() {
	return (
		<Block title="Charts">
			<Row label="AreaChart">
				<AreaChart className="w-full" data={DATA} series={SERIES} xKey="month" height={220} stacked showLegend />
			</Row>
			<Row label="BarChart">
				<BarChart className="w-full" data={DATA} series={SERIES} xKey="month" height={220} showLegend />
			</Row>
			<Row label="LineChart">
				<LineChart className="w-full" data={DATA} series={SERIES} xKey="month" height={220} showLegend />
			</Row>
			<Row label="PieChart">
				<PieChart className="w-64" data={PIE} height={220} showLegend />
				<PieChart className="w-64" data={PIE} height={220} innerRadius="55%" />
			</Row>
			<Row label="Sparkline">
				{SLOTS.map((i) => (
					<div key={i} className="w-24">
						<Sparkline data={SPARK.map((v) => v + i)} color={chartColor(i)} height={28} />
					</div>
				))}
			</Row>
			<Row label="Gauge">
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
		<SinkPage title="Charts" description="Every chart, with all 8 categorical slots where it takes several series.">
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
