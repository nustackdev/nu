import type { Meta, StoryObj } from "@storybook/react-vite";
import { LineChart } from "./line-chart";

const DATA = Array.from({ length: 12 }, (_, i) => ({
	x: `t${i + 1}`,
	traces: Math.round(200 + Math.sin(i * 0.5) * 80 + i * 8),
	errors: Math.round(8 + Math.cos(i * 0.3) * 5),
}));

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl">
				<LineChart
					data={DATA}
					xKey="x"
					series={[{ dataKey: "traces", name: "traces" }]}
				/>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl space-y-6">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						single series
					</div>
					<LineChart
						data={DATA}
						xKey="x"
						series={[{ dataKey: "traces", name: "traces" }]}
					/>
				</div>
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						two series + legend
					</div>
					<LineChart
						data={DATA}
						xKey="x"
						showLegend
						series={[
							{ dataKey: "traces", name: "traces" },
							{ dataKey: "errors", name: "errors" },
						]}
					/>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/LineChart",
};

export default meta;
