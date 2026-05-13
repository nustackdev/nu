// Renderer registry: Ref type name -> React component.
// Each component subscribes only to its own slice, so a write on one Ref
// re-renders just that component.

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useStore } from "./store";

type RendererProps = { path: string };

function TitleView({ path }: RendererProps) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	return <h1 className="text-3xl font-semibold">{value}</h1>;
}

function IntView({ path }: RendererProps) {
	const value = useStore((s) => (s.refs[path]?.value as number) ?? 0);
	return <span className="font-mono text-2xl">{value}</span>;
}

type LineChartValue = { points: [number, number][] };

function LineChartView({ path }: RendererProps) {
	const points = useStore((s) => (s.refs[path]?.value as LineChartValue | undefined)?.points ?? []);
	const data = points.map(([x, y]) => ({ x, y }));
	return (
		<div className="h-64 w-full">
			<ResponsiveContainer width="100%" height="100%">
				<LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
					<XAxis dataKey="x" type="number" domain={["dataMin", "dataMax"]} />
					<YAxis />
					<Tooltip />
					<Line type="monotone" dataKey="y" dot={false} isAnimationActive={false} />
				</LineChart>
			</ResponsiveContainer>
		</div>
	);
}

export const renderers: Record<string, React.FC<RendererProps>> = {
	TitleRef: TitleView,
	IntRef: IntView,
	LineChart: LineChartView,
};
