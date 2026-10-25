// Refs/Grid: the Grid node as a program draws it. Cards of stats and
// sparklines in equal cells, a gallery that fits as many as the width
// allows, charts that take their cell's width, and a bento of spanning
// cells that collapses to a stack when the grid narrows.

import type { ChainStep, TreeFrame } from "@nustackdev/ui-core";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { chartSet, chartStep } from "./chart-samples";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Grid",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

const STATS = [
	{
		title: "Runs",
		value: "1,284",
		delta: "+ 12.4%",
		trend: "up",
		points: [4, 6, 5, 8, 7, 9, 12, 11, 14],
	},
	{
		title: "Tokens",
		value: "842k",
		delta: "- 3.1%",
		trend: "down",
		points: [9, 8, 9, 7, 6, 7, 5, 6, 5],
	},
	{
		title: "Errors",
		value: "0.9%",
		delta: "- 0.2 pp",
		trend: "down",
		points: [3, 4, 2, 3, 2, 2, 1, 2, 1],
	},
	{
		title: "Uptime",
		value: "99.94%",
		delta: "no change",
		trend: "flat",
		points: [5, 5, 5, 5, 4, 5, 5, 5, 5],
	},
	{ title: "Queue", value: "37", delta: "+ 4", trend: "up", points: [1, 2, 2, 3, 5, 4, 6, 7, 8] },
	{
		title: "p95",
		value: "182 ms",
		delta: "- 9 ms",
		trend: "down",
		points: [8, 9, 7, 8, 6, 7, 6, 5, 6],
	},
] as const;

export const StatCards: Story = {
	render: () => {
		const root = "grid-stats";
		const grid = step(root, "Grid", {
			columns: 3,
			min_width: 200,
			gap: 4,
			align: "stretch",
			padding: 0,
		});
		const chains: ChainStep[][] = [];
		const frames: TreeFrame[] = [];
		STATS.forEach((s, i) => {
			const card = step(`c${i}`, "Card", { title: s.title });
			chains.push([
				grid,
				card,
				step("stat", "StatRef", { label: "today", value: s.value, delta: s.delta, trend: s.trend }),
			]);
			chains.push([grid, card, chartStep("spark", "sparkline")]);
			frames.push({
				op: "merge",
				ref: [root, `c${i}`, "spark"],
				payload: { series: [{ data: [...s.points] }] },
			});
		});
		return (
			<NodeStage
				root={root}
				label="columns 3: six cards, a stat and a sparkline each"
				chains={chains}
				frames={frames}
			/>
		);
	},
};

export const Gallery: Story = {
	render: () => {
		const root = "grid-gallery";
		const grid = step(root, "Grid", { columns: 0, min_width: 140, gap: 3 });
		const tones = ["ok", "info", "warn", "neutral"] as const;
		const chains: ChainStep[][] = Array.from({ length: 8 }, (_, i) => {
			const card = step(`t${i}`, "Card", { title: `Species ${i + 1}` });
			return [
				card,
				step("tag", "BadgeRef", {
					label: tones[i % tones.length],
					variant: tones[i % tones.length],
				}),
			];
		}).map((chain) => [grid, ...chain]);
		return (
			<NodeStage root={root} label="columns 0, min_width 140: as many as fit" chains={chains} />
		);
	},
};

export const Charts: Story = {
	render: () => {
		const root = "grid-charts";
		const grid = step(root, "Grid", { columns: 2, min_width: 220, gap: 4 });
		const pie = step("pie", "Card", { title: "Jobs by state" });
		const line = step("line", "Card", { title: "Throughput" });
		return (
			<NodeStage
				root={root}
				label="columns 2: a donut PieChart and a tall Sparkline, each its cell's width"
				chains={[
					[grid, pie, chartStep("chart", "donut")],
					[grid, line, chartStep("chart", "sparkline", { height: 160 })],
				]}
				frames={[
					chartSet([root, "pie", "chart"], "donut"),
					{
						op: "merge",
						ref: [root, "line", "chart"],
						payload: { series: [{ data: [12, 18, 15, 24, 22, 30, 27] }] },
					},
				]}
			/>
		);
	},
};

export const Bento: Story = {
	render: () => {
		const root = "grid-bento";
		const grid = step(root, "Grid", {
			columns: 4,
			min_width: 140,
			gap: 3,
			align: "stretch",
			padding: 0,
			dense: true,
			spans: {
				trend: { cols: 2, rows: 2 },
				split: { cols: 3, rows: 1 },
				side: { cols: 1, rows: 2 },
			},
		});
		const small = (seg: string, title: string, value: string): ChainStep[][] => [
			[grid, step(seg, "Card", { title })],
			[grid, step(seg, "Card"), step("stat", "StatRef", { label: "today", value })],
		];
		const trend = step("trend", "Card", { title: "Throughput", subtitle: "2 by 2" });
		const split = step("split", "Card", { title: "Two thirds", subtitle: "3 wide" });
		const side = step("side", "Card", { title: "Side", subtitle: "2 tall" });
		return (
			<NodeStage
				root={root}
				label="columns 4, dense, spans {trend: 2x2, split: 3x1, side: 1x2}; narrow it and the spans clamp, then stack"
				chains={[
					[grid, trend, chartStep("chart", "sparkline", { height: 180 })],
					...small("runs", "Runs", "1,284"),
					...small("tokens", "Tokens", "842k"),
					...small("errors", "Errors", "0.9%"),
					...small("queue", "Queue", "37"),
					[
						grid,
						split,
						step("note", "TextRef", {
							value: "A 2/3 + 1/3 split is a 3 wide cell beside a plain one in a 4 column grid.",
						}),
					],
					[grid, side, step("note", "TextRef", { value: "Two rows tall." })],
					...small("p95", "p95", "182 ms"),
				]}
				frames={[
					{
						op: "merge",
						ref: [root, "trend", "chart"],
						payload: { series: [{ data: [12, 18, 15, 24, 22, 30, 27, 33, 31] }] },
					},
				]}
			/>
		);
	},
};
