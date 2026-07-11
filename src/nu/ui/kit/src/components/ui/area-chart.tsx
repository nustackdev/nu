// AreaChart primitive. Thin recharts wrapper with kit-tokened chrome.
//
// Design refs:
//   primitives.md    §AreaChart (fill uses series color at 20% alpha via stop)
//   palette.md       chart-1..8 CSS vars for categorical scale
//
// Gradient fills: each series gets its own <linearGradient> with stops at 0.2
// alpha (opening) and 0.02 (fading out). Same technique the recharts examples
// use; alpha is expressed via stopOpacity so the CSS var still resolves.

import * as React from "react";
import {
	Area,
	AreaChart as RechartsAreaChart,
	CartesianGrid,
	Legend,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

import { cn } from "../../lib/utils";
import { chartAxisTick, chartColor, chartGridStroke, ChartTooltipContent } from "./chart-shared";

export interface AreaChartSeries {
	dataKey: string;
	name?: string;
	color?: string;
}

export interface AreaChartProps extends React.HTMLAttributes<HTMLDivElement> {
	data: Array<Record<string, unknown>>;
	series: AreaChartSeries[];
	xKey: string;
	height?: number;
	showGrid?: boolean;
	showTooltip?: boolean;
	showLegend?: boolean;
	stacked?: boolean;
}

export function AreaChart({
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
}: AreaChartProps) {
	// Stable gradient id namespace so multiple AreaCharts on the same page do
	// not collide. React 19's useId() gives a per-instance suffix.
	const gradId = React.useId();

	return (
		<div
			data-slot="area-chart"
			className={cn("w-full", className)}
			style={{ height }}
			{...props}
		>
			<ResponsiveContainer width="100%" height="100%">
				<RechartsAreaChart
					data={data}
					margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
				>
					<defs>
						{series.map((s, i) => {
							const color = s.color ?? chartColor(i);
							const id = `area-grad-${gradId}-${i}`;
							return (
								<linearGradient
									key={id}
									id={id}
									x1="0"
									y1="0"
									x2="0"
									y2="1"
								>
									<stop offset="0%" stopColor={color} stopOpacity={0.2} />
									<stop offset="100%" stopColor={color} stopOpacity={0.02} />
								</linearGradient>
							);
						})}
					</defs>
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
					{series.map((s, i) => {
						const color = s.color ?? chartColor(i);
						return (
							<Area
								key={s.dataKey}
								type="monotone"
								dataKey={s.dataKey}
								name={s.name ?? s.dataKey}
								stroke={color}
								strokeWidth={2}
								fill={`url(#area-grad-${gradId}-${i})`}
								stackId={stacked ? "stack" : undefined}
								isAnimationActive={false}
							/>
						);
					})}
				</RechartsAreaChart>
			</ResponsiveContainer>
		</div>
	);
}
