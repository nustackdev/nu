// LineChart -- time-series, recharts.

import {
	Line,
	LineChart as RcLineChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

type LineChartValue = { points: [number, number][] };

const factory: SliceFactory = (path, ctx) => ({
	type: "LineChart",
	value: { points: [] } as LineChartValue,
	write: (v) =>
		ctx.set((refs) => {
			refs[path].value = v as LineChartValue;
		}),
	append: (v) =>
		ctx.set((refs) => {
			const cur = refs[path].value as LineChartValue;
			cur.points.push(v as [number, number]);
		}),
});

function LineChartView({ path }: { path: string }) {
	const points = useStore((s) => (s.refs[path]?.value as LineChartValue | undefined)?.points ?? []);
	const data = points.map(([x, y]) => ({ x, y }));
	return (
		<div className="h-64 w-full">
			<ResponsiveContainer width="100%" height="100%">
				<RcLineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
					<XAxis dataKey="x" type="number" domain={["dataMin", "dataMax"]} />
					<YAxis />
					<Tooltip />
					<Line type="monotone" dataKey="y" dot={false} isAnimationActive={false} />
				</RcLineChart>
			</ResponsiveContainer>
		</div>
	);
}

export const LineChart: RefEntry = { factory, component: LineChartView };
