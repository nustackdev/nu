// Shared chart chrome for the recharts wrappers (Line/Bar/Area/Pie/Sparkline).
//
// Centralizes the token-aware tooltip content, the axis tick style, and the
// grid/axis stroke color so every chart primitive stays consistent without
// re-declaring the same tokens.

// Categorical scale references CSS vars from index.css §chart-1..8.
// 8 slots is enough for the vast majority of dashboards; consumers who need
// more should pass explicit per-series `color` overrides.
export const CHART_PALETTE_SIZE = 8;

export function chartColor(index: number): string {
	// 1-indexed CSS vars; wrap so extra series still resolve to a valid color.
	const slot = (index % CHART_PALETTE_SIZE) + 1;
	return `var(--chart-${slot})`;
}

// Grid + axis lines share the subtle border color so the chart chrome recedes.
export const chartGridStroke = "var(--border-subtle)";

// Axis tick style: mono numerals + muted text at the tightest text step, per
// typography.md §4 chart tick labels. Kept as a plain object so the shape stays
// assignable to recharts' picky `TickProp` union (SVG text props subset).
export const chartAxisTick = {
	fill: "var(--text-muted)",
	fontSize: 11,
	fontFamily: "var(--font-mono)",
} as const;

// Payload shape recharts hands the tooltip. We type just what we read.
interface TooltipPayloadItem {
	name?: string | number;
	value?: string | number;
	color?: string;
	dataKey?: string | number;
	payload?: Record<string, unknown>;
}

export interface ChartTooltipContentProps {
	active?: boolean;
	payload?: TooltipPayloadItem[];
	label?: string | number;
}

// Tooltip content shell: elevated surface, subtle border, primary text.
// A recharts-style shape so it drops in via <Tooltip content={...} />.
export function ChartTooltipContent({
	active,
	payload,
	label,
}: ChartTooltipContentProps) {
	if (!active || !payload || payload.length === 0) return null;
	return (
		<div
			data-slot="chart-tooltip"
			className="rounded-md border border-border-subtle bg-bg-elevated px-2.5 py-1.5 text-xs text-text-primary shadow-sm"
		>
			{label !== undefined && (
				<div className="text-text-muted font-mono mb-1">{String(label)}</div>
			)}
			<div className="flex flex-col gap-0.5">
				{payload.map((item, i) => (
					<div
						key={`${item.dataKey ?? i}`}
						className="flex items-center gap-2"
					>
						<span
							aria-hidden="true"
							className="inline-block size-2 rounded-full"
							style={{ backgroundColor: item.color }}
						/>
						<span className="text-text-secondary">{item.name}</span>
						<span className="ml-auto font-mono">{String(item.value ?? "")}</span>
					</div>
				))}
			</div>
		</div>
	);
}
