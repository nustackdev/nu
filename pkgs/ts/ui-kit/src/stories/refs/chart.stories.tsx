// Refs/Charts: the Chart node as a program draws it, a story per family.
//
// Each chart is a `Chart` chain level with the props its Python builder's
// slot declares, then the `merge` frame its `set(data)` sends (both from
// chart-samples.json). Streaming appends live through the store the way
// `append` frames land; Merge and clear shows the other two ops.

import type { ChainStep, TreeFrame } from "@nustackdev/ui-core";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect } from "react";
import { tree } from "../../tree";
import { chartSet, chartStep, type SampleName, sample } from "./chart-samples";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Charts",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

/** A column of charts under `root`, each set to its sample's data. */
function family(root: string, label: string, names: SampleName[]) {
	const col = step(root, "Column", { gap: 6 });
	const chains: ChainStep[][] = [[col]];
	const frames: TreeFrame[] = [];
	for (const name of names) {
		chains.push([col, chartStep(name, name)]);
		frames.push(chartSet([root, name], name));
	}
	return <NodeStage root={root} label={label} chains={chains} frames={frames} />;
}

export const Lines: Story = {
	render: () =>
		family("charts-lines", "LineChart over categories and time, AreaChart stacked", [
			"line",
			"line-time",
			"area-stacked",
		]),
};

export const Bars: Story = {
	render: () =>
		family("charts-bars", "BarChart grouped, stacked, horizontal with labels; Histogram", [
			"bar",
			"bar-stacked",
			"bar-horizontal",
			"histogram",
		]),
};

export const Distributions: Story = {
	render: () =>
		family("charts-dist", "ScatterChart, BoxplotChart, CandlestickChart, HeatmapChart", [
			"scatter",
			"boxplot",
			"candlestick",
			"heatmap",
		]),
};

export const PartsOfAWhole: Story = {
	render: () =>
		family("charts-parts", "PieChart, a donut with its total, FunnelChart", [
			"pie",
			"donut",
			"funnel",
		]),
};

export const Hierarchies: Story = {
	render: () =>
		family("charts-tree", "TreemapChart and SunburstChart from one nested mapping", [
			"treemap",
			"sunburst",
		]),
};

export const FlowsAndMeasures: Story = {
	render: () =>
		family("charts-flows", "SankeyChart, RadarChart, GaugeChart", ["sankey", "radar", "gauge"]),
};

export const InACard: Story = {
	render: () => {
		const root = "charts-cards";
		const grid = step(root, "Grid", { columns: 3, min_width: 160, gap: 4 });
		const chains: ChainStep[][] = [];
		const frames: TreeFrame[] = [];
		["Runs", "Tokens", "Errors"].forEach((title, i) => {
			const card = step(`c${i}`, "Card", { title });
			chains.push([grid, card, chartStep("spark", "sparkline")]);
			frames.push({
				op: "merge",
				ref: [root, `c${i}`, "spark"],
				payload: {
					color: [`var(--chart-${i + 1})`],
					series: [{ data: Array.from({ length: 16 }, (_, k) => 5 + ((k * (i + 3)) % 7) + k / 3) }],
				},
			});
		});
		return (
			<NodeStage
				root={root}
				label="Sparkline in cards, colored with kit tokens"
				chains={chains}
				frames={frames}
			/>
		);
	},
};

// Appends one point per series every 250 ms, as `append` frames from a
// server would. `max_points` is 40, so the window slides once it fills, and
// the third series appears by name partway through.
function Streaming() {
	const root = "charts-stream";
	useEffect(() => {
		let t = 0;
		const id = setInterval(() => {
			t++;
			const send = (series: string, y: number) =>
				tree.getState().dispatch({
					op: "append",
					ref: [root, "live"],
					payload: { series, points: [[t, Math.round(y * 10) / 10]] },
				});
			send("cpu", 50 + 25 * Math.sin(t / 6));
			send("mem", 60 + 10 * Math.cos(t / 9));
			if (t > 20) send("gpu", 30 + 20 * Math.sin(t / 4));
		}, 250);
		return () => clearInterval(id);
	}, []);
	const col = step(root, "Column", { gap: 4 });
	return (
		<NodeStage
			root={root}
			label="append every 250 ms, max_points 40; gpu joins by name at t=21"
			chains={[
				[col],
				[
					col,
					chartStep("live", "line-time", {
						max_points: 40,
						option: {
							...sample("line-time").props.option,
							xAxis: { type: "value", scale: true },
							animation: false,
						},
					}),
				],
			]}
		/>
	);
}

export const Stream: Story = {
	name: "Streaming",
	render: () => <Streaming />,
};

export const MergeAndClear: Story = {
	render: () => {
		const root = "charts-ops";
		const col = step(root, "Column", { gap: 6 });
		return (
			<NodeStage
				root={root}
				label="merge retitles the bars and recolors a series; clear empties Series 2"
				chains={[[col], [col, chartStep("bars", "bar")]]}
				frames={[
					chartSet([root, "bars"], "bar"),
					{
						op: "merge",
						ref: [root, "bars"],
						payload: {
							title: [{ id: "title", text: "Sightings, merged" }],
							series: [{ name: "Series 4", itemStyle: { color: "var(--status-danger)" } }],
						},
					},
					{ op: "clear", ref: [root, "bars"], payload: { series: "Series 2" } },
				]}
			/>
		);
	},
};
