import type { Meta, StoryObj } from "@storybook/react-vite";
import { PieChart } from "./pie-chart";

const DATA = [
	{ name: "traces", value: 62 },
	{ name: "logs", value: 24 },
	{ name: "metrics", value: 14 },
];

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
				<PieChart data={DATA} />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						pie
					</div>
					<div className="max-w-md">
						<PieChart data={DATA} showLegend />
					</div>
				</div>
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						donut
					</div>
					<div className="max-w-md">
						<PieChart data={DATA} innerRadius="60%" showLegend />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/PieChart",
};

export default meta;
