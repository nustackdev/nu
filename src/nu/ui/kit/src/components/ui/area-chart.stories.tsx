import type { Meta, StoryObj } from "@storybook/react-vite";
import { AreaChart } from "./area-chart";

const DATA = Array.from({ length: 20 }, (_, i) => ({
	t: `t${i + 1}`,
	a: Math.round(120 + Math.sin(i * 0.4) * 60),
	b: Math.round(80 + Math.cos(i * 0.5) * 40),
}));

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl">
				<AreaChart
					data={DATA}
					xKey="t"
					series={[{ dataKey: "a", name: "series a" }]}
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
					<AreaChart
						data={DATA}
						xKey="t"
						series={[{ dataKey: "a", name: "series a" }]}
					/>
				</div>
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						stacked
					</div>
					<AreaChart
						data={DATA}
						xKey="t"
						stacked
						showLegend
						series={[
							{ dataKey: "a", name: "series a" },
							{ dataKey: "b", name: "series b" },
						]}
					/>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/AreaChart",
};

export default meta;
