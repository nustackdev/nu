import type { Meta, StoryObj } from "@storybook/react-vite";
import { BarChart } from "./bar-chart";

const DATA = [
	{ day: "Mon", runs: 42, errors: 3 },
	{ day: "Tue", runs: 55, errors: 5 },
	{ day: "Wed", runs: 78, errors: 4 },
	{ day: "Thu", runs: 63, errors: 7 },
	{ day: "Fri", runs: 92, errors: 2 },
	{ day: "Sat", runs: 34, errors: 1 },
	{ day: "Sun", runs: 28, errors: 0 },
];

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl">
				<BarChart
					data={DATA}
					xKey="day"
					series={[{ dataKey: "runs", name: "runs" }]}
				/>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl space-y-6">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						grouped
					</div>
					<BarChart
						data={DATA}
						xKey="day"
						showLegend
						series={[
							{ dataKey: "runs", name: "runs" },
							{ dataKey: "errors", name: "errors" },
						]}
					/>
				</div>
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						stacked
					</div>
					<BarChart
						data={DATA}
						xKey="day"
						stacked
						showLegend
						series={[
							{ dataKey: "runs", name: "runs" },
							{ dataKey: "errors", name: "errors" },
						]}
					/>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/BarChart",
};

export default meta;
