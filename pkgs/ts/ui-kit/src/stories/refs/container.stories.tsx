// Refs/Container: the page frame as a program draws it. A heading, a line
// and a card stacked in a frame capped at a page width, centred, with the
// responsive side gutter; one story per width, and one edge to edge.

import type { ChainStep } from "@nustackdev/ui-core";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Container",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

function page(root: string, props: Record<string, unknown>): ChainStep[][] {
	const frame = step(root, "Container", props);
	const card = step("card", "Card", { title: "Shelf" });
	return [
		[frame, step("heading", "HeadingRef", { label: "Your movies" })],
		[frame, step("intro", "TextRef", { value: "Log what you watch. The frame stays centred." })],
		[frame, card, step("stat", "StatRef", { label: "Total", value: "42" })],
	];
}

function sized(size: string, label: string): Story {
	return {
		render: () => {
			const root = `container-${size}`;
			return <NodeStage root={root} label={label} chains={page(root, { max_width: size })} />;
		},
	};
}

export const Main = sized("main", "max_width main: 1200, the default");
export const Dashboard = sized("dashboard", "max_width dashboard: 1400");
export const Panel = sized("panel", "max_width panel: 960");
export const Prose = sized("prose", "max_width prose: 640");
export const FormWidth = sized("form", "max_width form: 480");

export const EdgeToEdge: Story = {
	render: () => {
		const root = "container-edge";
		return (
			<NodeStage
				root={root}
				label="max_width full, padding 0: no cap, no gutter"
				chains={page(root, { max_width: "full", padding: 0, gap: 4 })}
			/>
		);
	},
};
