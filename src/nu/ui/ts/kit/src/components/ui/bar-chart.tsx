// BarChart primitive. Thin recharts wrapper with kit-tokened chrome.
//
// Design refs:
//   primitives.md    §BarChart
//   palette.md       chart-1..8 CSS vars for categorical scale

import type * as React from "react";
import {
	Bar,
	BarChart as RechartsBarChart,
	CartesianGrid,
	Legend,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

import { cn } from "../../lib/utils";
import { chartAxisTick, chartColor, chartGridStroke, ChartTooltipContent } from "./chart-shared";

export interface BarChartSeries {
	dataKey: string;
	name?: string;
	color?: string;
}

export interface BarChartProps extends React.HTMLAttributes<HTMLDivElement> {
	data: Array<Record<string, unknown>>;
	series: BarChartSeries[];
	xKey: string;
	height?: number;
	showGrid?: boolean;
	showTooltip?: boolean;
	showLegend?: boolean;
	stacked?: boolean;
}

export function BarChart({
	className,
	data,
	series,
	xKey,
	height = 240,
	showGrid = true,
	showTooltip = true,
	showLegend = false,
	stacked = false,
	...props
}: BarChartProps) {
	return (
		<div
			data-slot="bar-chart"
			className={cn("w-full", className)}
			style={{ height }}
			{...props}
		>
			<ResponsiveContainer width="100%" height="100%">
				<RechartsBarChart
					data={data}
					margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
				>
					{showGrid && (
						<CartesianGrid
							stroke={chartGridStroke}
							strokeDasharray="3 3"
							vertical={false}
						/>
					)}
					<XAxis
						dataKey={xKey}
						tick={chartAxisTick}
						tickLine={false}
						axisLine={{ stroke: chartGridStroke }}
					/>
					<YAxis
						tick={chartAxisTick}
						tickLine={false}
						axisLine={{ stroke: chartGridStroke }}
					/>
					{showTooltip && (
						<Tooltip
							content={<ChartTooltipContent />}
							cursor={{ fill: "var(--accent-wash)" }}
						/>
					)}
					{showLegend && (
						<Legend
							wrapperStyle={{ fontSize: 11, color: "var(--text-muted)" }}
						/>
					)}
					{series.map((s, i) => (
						<Bar
							key={s.dataKey}
							dataKey={s.dataKey}
							name={s.name ?? s.dataKey}
							fill={s.color ?? chartColor(i)}
							stackId={stacked ? "stack" : undefined}
							radius={[2, 2, 0, 0]}
							isAnimationActive={false}
						/>
					))}
				</RechartsBarChart>
			</ResponsiveContainer>
		</div>
	);
}
