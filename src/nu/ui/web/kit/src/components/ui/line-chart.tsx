// LineChart primitive. Thin recharts wrapper with kit-tokened chrome.
//
// Design refs:
//   primitives.md    §LineChart (props, tokens, motion notes)
//   palette.md       chart-1..8 CSS vars for categorical scale
//   typography.md    axis ticks + tooltip use font-mono text-xs / text-muted
//   a11y.md          §7 series color paired with marker for color-blind safety
//
// Colors are inline `var(--chart-N)` strings; recharts accepts CSS var strings
// for stroke/fill directly and re-resolves them per theme through :root/.dark.

import type * as React from "react";
import {
	CartesianGrid,
	Legend,
	Line,
	LineChart as RechartsLineChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

import { cn } from "../../lib/utils";
import { chartColor, ChartTooltipContent, chartAxisTick, chartGridStroke } from "./chart-shared";

export interface LineChartSeries {
	dataKey: string;
	name?: string;
	color?: string;
}

export interface LineChartProps extends React.HTMLAttributes<HTMLDivElement> {
	data: Array<Record<string, unknown>>;
	series: LineChartSeries[];
	xKey: string;
	height?: number;
	showGrid?: boolean;
	showTooltip?: boolean;
	showLegend?: boolean;
}

export function LineChart({
	className,
	data,
	series,
	xKey,
	height = 240,
	showGrid = true,
	showTooltip = true,
	showLegend = false,
	...props
}: LineChartProps) {
	return (
		<div
			data-slot="line-chart"
			className={cn("w-full", className)}
			style={{ height }}
			{...props}
		>
			<ResponsiveContainer width="100%" height="100%">
				<RechartsLineChart
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
						<Tooltip content={<ChartTooltipContent />} cursor={{ stroke: chartGridStroke }} />
					)}
					{showLegend && (
						<Legend
							wrapperStyle={{ fontSize: 11, color: "var(--text-muted)" }}
						/>
					)}
					{series.map((s, i) => (
						<Line
							key={s.dataKey}
							type="monotone"
							dataKey={s.dataKey}
							name={s.name ?? s.dataKey}
							stroke={s.color ?? chartColor(i)}
							strokeWidth={2}
							dot={false}
							activeDot={{ r: 4 }}
							isAnimationActive={false}
						/>
					))}
				</RechartsLineChart>
			</ResponsiveContainer>
		</div>
	);
}
