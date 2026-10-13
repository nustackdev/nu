import type { Meta, StoryObj } from "@storybook/react-vite";
import type * as React from "react";
import { useState } from "react";
import { ThemePair } from "../../stories/kitchen-sink/frame";
import { Button } from "./button";
import { SketchBoard, type SketchBoardProps } from "./sketch-board";
import {
	SKETCH_FILLS,
	SKETCH_SIZES,
	SKETCH_STROKES,
	type SketchElement,
} from "./sketch-board-model";

// Elements are plain data, the same JSON a program writes from Python.

const DIAGRAM: SketchElement[] = [
	{
		type: "rect",
		x: 0.06,
		y: 0.3,
		w: 0.24,
		h: 0.26,
		stroke: "blue",
		fill: "blue-soft",
		width: 0.008,
	},
	{
		type: "arrow",
		points: [
			[0.32, 0.43],
			[0.46, 0.43],
		],
		stroke: "ink",
		width: 0.008,
	},
	{
		type: "ellipse",
		x: 0.48,
		y: 0.28,
		w: 0.2,
		h: 0.3,
		stroke: "violet",
		fill: "violet-soft",
		width: 0.008,
	},
	{
		type: "arrow",
		points: [
			[0.7, 0.43],
			[0.84, 0.43],
		],
		stroke: "ink",
		width: 0.008,
	},
	{
		type: "rect",
		x: 0.86,
		y: 0.33,
		w: 0.1,
		h: 0.2,
		stroke: "green",
		fill: "green-soft",
		width: 0.008,
	},
	{
		type: "path",
		points: [
			[0.5, 0.68],
			[0.54, 0.7],
			[0.58, 0.67],
			[0.62, 0.71],
			[0.66, 0.68],
		],
		stroke: "red",
		width: 0.012,
	},
	{
		type: "line",
		points: [
			[0.06, 0.82],
			[0.96, 0.82],
		],
		stroke: "gray",
		width: 0.004,
	},
];

const SEVEN: SketchElement[] = [
	{
		type: "path",
		points: [
			[0.26, 0.24],
			[0.42, 0.23],
			[0.58, 0.23],
			[0.72, 0.24],
			[0.64, 0.38],
			[0.56, 0.52],
			[0.49, 0.66],
			[0.44, 0.8],
		],
		stroke: "ink",
		width: 0.07,
	},
];

/** All stroke colors as lines, all fills as tiles, all sizes as strokes. */
const SWATCHES: SketchElement[] = [
	...SKETCH_STROKES.map(
		(stroke, i): SketchElement => ({
			type: "line",
			points: [
				[0.06, 0.1 + i * 0.05],
				[0.44, 0.1 + i * 0.05],
			],
			stroke,
			width: 0.012,
		}),
	),
	...SKETCH_FILLS.map(
		(fill, i): SketchElement => ({
			type: "rect",
			x: 0.54 + (i % 4) * 0.11,
			y: 0.08 + Math.floor(i / 4) * 0.2,
			w: 0.09,
			h: 0.16,
			stroke: SKETCH_STROKES[Math.min(i, SKETCH_STROKES.length - 1)],
			fill,
			width: 0.006,
		}),
	),
	...SKETCH_SIZES.map(
		(width, i): SketchElement => ({
			type: "path",
			points: Array.from({ length: 24 }, (_, k): [number, number] => [
				0.06 + k * 0.038,
				0.6 + i * 0.1 + Math.sin(k / 2.2) * 0.025,
			]),
			stroke: "ink",
			width,
		}),
	),
];

function Board({
	initial = [],
	...props
}: Omit<SketchBoardProps, "value"> & { initial?: SketchElement[] }) {
	const [value, setValue] = useState<SketchElement[]>(initial);
	return (
		<div className="flex flex-col gap-2">
			<SketchBoard value={value} onValueChange={setValue} {...props} />
			<div className="font-mono text-xs text-text-muted">
				{value.length} {value.length === 1 ? "element" : "elements"}
			</div>
		</div>
	);
}

function Cell({
	title,
	note,
	children,
}: {
	title: string;
	note?: string;
	children: React.ReactNode;
}) {
	return (
		<div className="flex flex-col gap-2">
			<div>
				<div className="font-mono text-xs uppercase tracking-widest text-text-muted">{title}</div>
				{note && <div className="font-mono text-xs text-text-muted">{note}</div>}
			</div>
			{children}
		</div>
	);
}

/** One full board, every tool and control. Try P R O L A, mod+Z, shift to constrain. */
export const Playground: StoryObj = {
	render: () => (
		<div className="p-8">
			<Board width={720} height={460} label="Playground" />
		</div>
	),
};

/** The configs a program picks: full, pen only (the digit reader), shapes only, read-only. */
export const Configs: StoryObj = {
	render: () => (
		<div className="flex flex-wrap items-start gap-8 p-8">
			<Cell title="full toolbar" note="tools: all, controls: all">
				<Board width={440} height={300} />
			</Cell>
			<Cell title="pen only" note='tools: ["pen"], controls: ["clear"], size 0.07'>
				<Board width={280} tools={["pen"]} controls={["clear"]} defaults={{ size: 0.07 }} />
			</Cell>
			<Cell title="shapes only" note="rect, ellipse, line, arrow; stroke, fill, undo">
				<Board
					width={440}
					height={300}
					tools={["rect", "ellipse", "line", "arrow"]}
					controls={["tools", "stroke", "fill", "undo", "redo", "clear"]}
				/>
			</Cell>
			<Cell title="no toolbar" note="controls: [], pen only">
				<Board width={280} tools={["pen"]} controls={[]} />
			</Cell>
			<Cell title="read-only" note="a preset drawing, no input">
				<SketchBoard value={DIAGRAM} width={440} height={300} readonly />
			</Cell>
		</div>
	),
};

/** Width and height in px; the aspect holds as the container narrows. */
export const Sizes: StoryObj = {
	render: () => (
		<div className="flex flex-wrap items-start gap-8 p-8">
			<Cell title="280 square">
				<Board width={280} initial={SEVEN} />
			</Cell>
			<Cell title="480 x 270" note="16:9">
				<Board width={480} height={270} initial={DIAGRAM} />
			</Cell>
			<Cell title="240 x 360" note="tall">
				<Board width={240} height={360} />
			</Cell>
			<Cell title="600 in a 320 column" note="shrinks, keeps 3:2">
				<div className="w-80">
					<Board width={600} height={400} initial={DIAGRAM} />
				</div>
			</Cell>
		</div>
	),
};

/** The palette and sizes, and boards that start from other defaults. */
export const Palettes: StoryObj = {
	render: () => (
		<div className="flex flex-wrap items-start gap-8 p-8">
			<Cell title="palette" note="strokes, fills, the four sizes">
				<SketchBoard value={SWATCHES} width={520} height={360} readonly />
			</Cell>
			<Cell title="red marker" note='defaults: stroke "red", size 0.024'>
				<Board width={320} defaults={{ stroke: "red", size: 0.024 }} />
			</Cell>
			<Cell title="blue arrows" note='defaults: tool "arrow", stroke "blue"'>
				<Board width={320} defaults={{ tool: "arrow", stroke: "blue", size: 0.012 }} />
			</Cell>
			<Cell title="green boxes" note='defaults: tool "rect", green on green-soft'>
				<Board width={320} defaults={{ tool: "rect", stroke: "green", fill: "green-soft" }} />
			</Cell>
			<Cell title="hex colors" note="any CSS color, drawn as is">
				<SketchBoard
					width={320}
					readonly
					value={[
						{
							type: "ellipse",
							x: 0.15,
							y: 0.15,
							w: 0.7,
							h: 0.7,
							stroke: "#e11d48",
							fill: "#fde68a",
							width: 0.02,
						},
					]}
				/>
			</Cell>
		</div>
	),
};

/** A program draws: each button writes elements the way `.set()` from Python does. */
export const AgentDraws: StoryObj = {
	render: function AgentDraws() {
		const [value, setValue] = useState<unknown[]>([]);
		return (
			<div className="flex flex-wrap items-start gap-6 p-8">
				<SketchBoard
					value={value}
					onValueChange={setValue}
					width={560}
					height={360}
					label="Agent board"
				/>
				<div className="flex flex-col gap-2">
					<Button variant="secondary" onClick={() => setValue(DIAGRAM)}>
						Draw a diagram
					</Button>
					<Button variant="secondary" onClick={() => setValue(SEVEN)}>
						Draw a 7
					</Button>
					<Button
						variant="secondary"
						onClick={() =>
							setValue([
								...value,
								{
									type: "arrow",
									points: [
										[Math.random(), Math.random()],
										[Math.random(), Math.random()],
									],
								},
							])
						}
					>
						Add an arrow
					</Button>
					<Button variant="ghost" onClick={() => setValue([])}>
						Clear
					</Button>
					<div className="max-w-56 font-mono text-xs text-text-muted">
						A write from outside replaces the board and starts its undo history over.
					</div>
				</div>
			</div>
		);
	},
};

/** Light and dark side by side. Popovers follow the page theme, not the column. */
export const DarkAndLight: StoryObj = {
	parameters: { layout: "fullscreen", themes: { themeOverride: "light" } },
	render: () => (
		<ThemePair>
			<div className="flex flex-wrap gap-6">
				<SketchBoard value={DIAGRAM} width={420} height={280} readonly />
				<Board width={420} height={280} initial={SWATCHES} />
			</div>
		</ThemePair>
	),
};

const meta: Meta = {
	title: "UI/SketchBoard",
};

export default meta;
