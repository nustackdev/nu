// PieChart primitive. Thin recharts wrapper with kit-tokened chrome.
//
// Design refs:
//   primitives.md    §PieChart (donut via innerRadius; centerLabel slot)
//   palette.md       chart-1..8 CSS vars for categorical scale
//
// Donut mode is opt-in via `innerRadius`. Value expressed as a percent string
// so recharts scales it against the container.

import type * as React from "react";
import {
	Cell,
	Legend,
	Pie,
	PieChart as RechartsPieChart,
	ResponsiveContainer,
	Tooltip,
} from "recharts";

import { cn } from "../../lib/utils";
import { chartColor, ChartTooltipContent } from "./chart-shared";

export interface PieChartDatum {
	name: string;
	value: number;
	color?: string;
}

export interface PieChartProps extends React.HTMLAttributes<HTMLDivElement> {
	data: PieChartDatum[];
	// nameKey defaults to "name", valueKey defaults to "value". Kept as props
	// so consumers can pass upstream row shapes without a reshape step.
	nameKey?: string;
	valueKey?: string;
	height?: number;
	// innerRadius > 0 turns the pie into a donut. Number = px; string = percent.
	innerRadius?: number | string;
	outerRadius?: number | string;
	showTooltip?: boolean;
	showLegend?: boolean;
}

export function PieChart({
	className,
	data,
	nameKey = "name",
	valueKey = "value",
	height = 240,
	innerRadius = 0,
	outerRadius = "80%",
	showTooltip = true,
	showLegend = false,
	...props
}: PieChartProps) {
	return (
		<div
			data-slot="pie-chart"
			className={cn("w-full", className)}
			style={{ height }}
			{...props}
		>
			<ResponsiveContainer width="100%" height="100%">
				<RechartsPieChart>
					<Pie
						data={data}
						dataKey={valueKey}
						nameKey={nameKey}
						innerRadius={innerRadius}
						outerRadius={outerRadius}
						strokeWidth={1}
						stroke="var(--bg-canvas)"
						isAnimationActive={false}
					>
						{data.map((d, i) => (
							<Cell
								key={d.name ?? i}
								fill={d.color ?? chartColor(i)}
							/>
						))}
					</Pie>
					{showTooltip && <Tooltip content={<ChartTooltipContent />} />}
					{showLegend && (
						<Legend
							wrapperStyle={{ fontSize: 11, color: "var(--text-muted)" }}
						/>
					)}
				</RechartsPieChart>
			</ResponsiveContainer>
		</div>
	);
}
