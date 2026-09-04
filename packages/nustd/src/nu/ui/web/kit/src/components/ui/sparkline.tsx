// Sparkline primitive. Tiny inline chart, no axes / grid, table-cell friendly.
//
// Design refs:
//   primitives.md    §Sparkline (24-40 h, no dots, tooltip off by default)
//   palette.md       chart-1 default; consumers can override via `color`

import * as React from "react";
import {
	Line,
	LineChart as RechartsLineChart,
	ResponsiveContainer,
	Tooltip,
} from "recharts";

import { cn } from "../../lib/utils";
import { chartColor, ChartTooltipContent } from "./chart-shared";

export interface SparklineProps extends React.HTMLAttributes<HTMLDivElement> {
	// Sparkline takes a raw number array for zero-friction table use; internal
	// reshape turns it into {v} records so recharts can render.
	data: number[];
	color?: string;
	height?: number;
	showTooltip?: boolean;
	showDots?: boolean;
}

export function Sparkline({
	className,
	data,
	color,
	height = 24,
	showTooltip = false,
	showDots = false,
	...props
}: SparklineProps) {
	const rows = React.useMemo(
		() => data.map((v, i) => ({ i, v })),
		[data],
	);
	const stroke = color ?? chartColor(0);
	return (
		<div
			data-slot="sparkline"
			className={cn("w-full", className)}
			style={{ height }}
			{...props}
		>
			<ResponsiveContainer width="100%" height="100%">
				<RechartsLineChart
					data={rows}
					margin={{ top: 2, right: 2, left: 2, bottom: 2 }}
				>
					{showTooltip && <Tooltip content={<ChartTooltipContent />} />}
					<Line
						type="monotone"
						dataKey="v"
						stroke={stroke}
						strokeWidth={1.5}
						dot={showDots ? { r: 1.5 } : false}
						activeDot={showTooltip ? { r: 3 } : false}
						isAnimationActive={false}
					/>
				</RechartsLineChart>
			</ResponsiveContainer>
		</div>
	);
}
