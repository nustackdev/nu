import type { Meta, StoryObj } from "@storybook/react-vite";
import type * as React from "react";
import { useEffect, useRef, useState } from "react";
import { type SampleName, sampleOption } from "../../stories/refs/chart-samples";
import { Chart, type ChartClick, type ChartHandle, type ChartOption } from "./chart";

// The primitive on its own: one option in, one chart out. The typed samples
// are the options the Python builders produce; the rest are raw options.

const ALL: SampleName[] = [
	"line",
	"line-time",
	"area-stacked",
	"bar",
	"bar-stacked",
	"bar-horizontal",
	"scatter",
	"histogram",
	"pie",
	"donut",
	"funnel",
	"heatmap",
	"radar",
	"treemap",
	"sunburst",
	"sankey",
	"gauge",
	"boxplot",
	"candlestick",
	"sparkline",
];

const RAW: ChartOption = {
	tooltip: { trigger: "axis" },
	xAxis: { type: "category", data: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] },
	yAxis: { type: "value" },
	series: [{ type: "line", name: "visits", smooth: true, data: [120, 200, 150, 80, 70, 110, 130] }],
};

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<Chart option={RAW} />
		</div>
	),
};

export const Typed: StoryObj = {
	name: "Every typed option",
	render: () => (
		<div className="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-6 p-8">
			{ALL.map((name) => (
				<div key={name} className="flex min-w-0 flex-col gap-2">
					<div className="font-mono text-xs uppercase tracking-widest text-text-muted">{name}</div>
					<Chart option={sampleOption(name)} />
				</div>
			))}
		</div>
	),
};

export const Full: StoryObj = {
	name: "Raw option, full build",
	render: () => (
		<div className="p-8">
			<Chart
				option={{
					angleAxis: { type: "category", data: ["N", "NE", "E", "SE", "S", "SW", "W", "NW"] },
					radiusAxis: {},
					polar: {},
					tooltip: {},
					series: [
						{ type: "bar", coordinateSystem: "polar", name: "wind", data: [4, 7, 12, 9, 5, 3, 6, 8] },
					],
				}}
			/>
		</div>
	),
};

function Streaming() {
	const chart = useRef<ChartHandle>(null);
	const data = useRef<[number, number][]>([]);
	useEffect(() => {
		let t = 0;
		const id = setInterval(() => {
			t += 1;
			data.current = [...data.current, [t, Math.round(50 + 30 * Math.sin(t / 5))] as [number, number]].slice(-60);
			chart.current?.patch({ series: [{ id: "s", data: data.current }] });
		}, 250);
		return () => clearInterval(id);
	}, []);
	return (
		<Chart
			ref={chart}
			option={{
				xAxis: { type: "value", scale: true },
				yAxis: { type: "value", min: 0, max: 100 },
				series: [{ id: "s", type: "line", smooth: true, showSymbol: false, data: [] }],
			}}
		/>
	);
}

export const Patch: StoryObj = {
	name: "Patch handle (streaming)",
	render: () => (
		<div className="p-8">
			<Streaming />
		</div>
	),
};

function Clicks() {
	const [last, setLast] = useState<ChartClick | null>(null);
	return (
		<div className="flex flex-col gap-3">
			<Chart option={sampleOption("pie")} onPointClick={setLast} />
			<div className="font-mono text-xs text-text-muted">
				{last ? `clicked ${last.name}: ${String(last.value)}` : "click a slice"}
			</div>
		</div>
	);
}

export const PointClick: StoryObj = {
	name: "Point click",
	render: () => (
		<div className="p-8">
			<Clicks />
		</div>
	),
};

// Tapped once at load, in the middle of the plot: on touch (a phone, or the
// Touch toolbar) the tooltip opens on that tap and stays inside the chart, on
// desktop a click opens it too. A narrow box (a phone, the Frame toolbar)
// draws fewer ticks on the value axis.
const DENSE: ChartOption = {
	tooltip: { trigger: "axis" },
	legend: {},
	xAxis: {
		type: "category",
		data: Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, "0")}:00`),
	},
	yAxis: { type: "value" },
	series: [
		{
			type: "line",
			name: "requests",
			showSymbol: false,
			data: Array.from({ length: 24 }, (_, i) => Math.round(900 + 600 * Math.sin(i / 3.5))),
		},
		{
			type: "line",
			name: "errors",
			showSymbol: false,
			data: Array.from({ length: 24 }, (_, i) => Math.round(120 + 80 * Math.cos(i / 2.5))),
		},
	],
};

// Taps the middle of the plot once the chart has drawn, the way a finger
// would: down, up, click.
function TapAtLoad({ children }: { children: React.ReactNode }) {
	const root = useRef<HTMLDivElement>(null);
	useEffect(() => {
		let live = true;
		const tap = async () => {
			const end = Date.now() + 8000;
			let canvas: HTMLCanvasElement | null = null;
			while (live && !canvas && Date.now() < end) {
				canvas = root.current?.querySelector("canvas") ?? null;
				if (!canvas) await new Promise((r) => setTimeout(r, 100));
			}
			// Past the entry animation, so the tooltip lands on the drawn line.
			// Asked again after: the first draw can be replaced (a theme read
			// at load re-inits), and the old canvas is gone.
			await new Promise((r) => setTimeout(r, 600));
			canvas = root.current?.querySelector("canvas") ?? null;
			if (!live || !canvas) return;
			const r = canvas.getBoundingClientRect();
			const at = {
				clientX: r.left + r.width * 0.55,
				clientY: r.top + r.height * 0.5,
				bubbles: true,
			};
			canvas.dispatchEvent(new MouseEvent("mousedown", at));
			canvas.dispatchEvent(new MouseEvent("mouseup", at));
			canvas.dispatchEvent(new MouseEvent("click", at));
		};
		tap();
		return () => {
			live = false;
		};
	}, []);
	return <div ref={root}>{children}</div>;
}

export const Tapped: StoryObj = {
	render: () => (
		<div className="p-4">
			<TapAtLoad>
				<Chart option={DENSE} />
			</TapAtLoad>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Chart",
};

export default meta;
