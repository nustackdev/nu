// Refs/Grid: the Grid node as a program draws it. Cards of stats and
// sparklines in equal cells, a gallery that fits as many as the width
// allows, and charts that take their cell's width.

import type { ChainStep, TreeFrame } from "@nustackdev/ui-core";
import type { Meta, StoryObj } from "@storybook/react-vite";
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
			chains.push([grid, card, step("spark", "Sparkline", { height: 32 })]);
			frames.push({
				op: "write",
				ref: [root, `c${i}`, "spark"],
				payload: { points: [...s.points] },
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
				label="columns 2: a PieChart and a LineChart, each its cell's width"
				chains={[
					[
						grid,
						pie,
						step("chart", "PieChart", {
							slices: [
								["done", 62],
								["running", 21],
								["queued", 12],
								["failed", 5],
							],
							inner_radius: 0.6,
							show_labels: false,
						}),
					],
					[grid, line, step("chart", "LineChart", { show_tooltip: false })],
				]}
				frames={[
					{
						op: "write",
						ref: [root, "line", "chart"],
						payload: {
							points: [
								[1, 12],
								[2, 18],
								[3, 15],
								[4, 24],
								[5, 22],
								[6, 30],
								[7, 27],
							],
						},
					},
				]}
			/>
		);
	},
};
