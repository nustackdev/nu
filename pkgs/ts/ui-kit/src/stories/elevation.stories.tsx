// Elevation: the four levels, light and dark side by side, each drawn with the
// exact recipe components use, then stacked so the steps read against each
// other.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { Text } from "../components/ui/text";
import { cn } from "../lib/utils";
import { ThemePair, sinkParameters } from "./kitchen-sink/frame";

type Level = {
	n: number;
	name: string;
	recipe: string;
	classes: string;
	uses: string;
};

const LEVELS: Level[] = [
	{
		n: 0,
		name: "flat",
		recipe: "bg-bg-surface border-border-default, no shadow",
		classes: "bg-bg-surface border border-border-default",
		uses: "cards and panels in a document, inputs, tables",
	},
	{
		n: 1,
		name: "raised",
		recipe: "bg-bg-elevated border-border-default shadow-raised",
		classes: "bg-bg-elevated border border-border-default shadow-raised",
		uses: "elevated card and panel, segmented tab thumb",
	},
	{
		n: 2,
		name: "floating",
		recipe: "bg-bg-elevated border-border-default shadow-floating",
		classes: "bg-bg-elevated border border-border-default shadow-floating",
		uses: "menus, popover, select, combobox, date picker, tooltips",
	},
	{
		n: 3,
		name: "modal",
		recipe: "bg-bg-elevated border-border-default shadow-modal, over bg-bg-overlay",
		classes: "bg-bg-elevated border border-border-default shadow-modal",
		uses: "dialog, sheet, command palette",
	},
];

function Tile({ level }: { level: Level }) {
	return (
		<div className={cn("flex flex-col gap-1 rounded-lg p-4", level.classes)}>
			<Text size="sm" className="font-medium">
				{level.n} {level.name}
			</Text>
			<Text size="xs" tone="muted" mono>
				{level.recipe}
			</Text>
			<Text size="xs" tone="secondary">
				{level.uses}
			</Text>
		</div>
	);
}

export const Levels: StoryObj = {
	parameters: sinkParameters,
	render: () => (
		<ThemePair>
			<div className="grid grid-cols-1 gap-8 rounded-lg bg-bg-canvas py-2">
				{LEVELS.map((l) => (
					<Tile key={l.n} level={l} />
				))}
			</div>
		</ThemePair>
	),
};

/** The levels on top of each other, the way they meet in an app. Positions
 * are inline: this is a picture, not a layout. */
export const Stack: StoryObj = {
	parameters: sinkParameters,
	render: () => (
		<ThemePair>
			<div className="relative rounded-lg border border-border-subtle bg-bg-canvas" style={{ height: 400 }}>
				<div className="p-4">
					<Text size="xs" tone="muted" mono>
						page
					</Text>
					<div className={cn("mt-3 rounded-lg p-4", LEVELS[0].classes)} style={{ width: 240 }}>
						<Text size="sm">0 flat card</Text>
					</div>
					<div className={cn("mt-3 rounded-lg p-4", LEVELS[1].classes)} style={{ width: 240 }}>
						<Text size="sm">1 raised card</Text>
					</div>
				</div>
				<div
					className={cn("absolute rounded-md p-1", LEVELS[2].classes)}
					style={{ top: 96, left: 200, width: 200 }}
				>
					{["Rename", "Duplicate", "Delete"].map((item, i) => (
						<div
							key={item}
							className={cn("rounded-sm px-2 py-1.5 text-sm", i === 1 && "bg-bg-hover")}
						>
							{item}
						</div>
					))}
				</div>
				<div
					className="absolute inset-x-0 bottom-0 rounded-b-lg bg-bg-overlay"
					style={{ height: 150 }}
				/>
				<div
					className={cn("absolute rounded-lg p-4", LEVELS[3].classes)}
					style={{ right: 24, bottom: 24, width: 240 }}
				>
					<Text size="sm" className="font-medium">
						3 modal
					</Text>
					<Text size="xs" tone="secondary">
						Over the scrim.
					</Text>
				</div>
			</div>
		</ThemePair>
	),
};

const meta: Meta = {
	title: "Docs/Elevation",
};

export default meta;
