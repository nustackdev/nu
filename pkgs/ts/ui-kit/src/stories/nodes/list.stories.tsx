// Nodes/List: the ListRef node as a program draws it. Plain string items
// first, then any child node as one more item, bulleted and numbered.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Nodes/List",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

export const Strings: Story = {
	render: () => (
		<NodeStage
			root="list-strings"
			label="items only, then one appended"
			chains={[[step("list-strings", "ListRef", { items: ["alpha", "beta"], variant: "bullet" })]]}
			frames={[{ op: "append", ref: ["list-strings"], payload: "gamma" }]}
		/>
	),
};

export const Children: Story = {
	render: () => {
		const list = step("list-children", "ListRef", { items: ["a plain string first"] });
		return (
			<NodeStage
				root="list-children"
				label="strings, then a Badge, a Link and a Row as items"
				chains={[
					[list, step("badge", "BadgeRef", { label: "live", variant: "ok" })],
					[list, step("link", "LinkRef", { label: "Read the docs", href: "https://nustack.dev" })],
					[list, step("row", "Row", { gap: 2, align: "center" })],
					[list, step("row", "Row"), step("k", "KbdRef", { label: "K" })],
					[list, step("row", "Row"), step("t", "TextRef", { value: "a Row as one item" })],
				]}
			/>
		);
	},
};

export const Numbered: Story = {
	render: () => {
		const list = step("list-numbered", "ListRef", {
			items: ["one", "two"],
			variant: "number",
			start: 1,
		});
		return (
			<NodeStage
				root="list-numbered"
				label="numbering runs on from the strings into the children"
				chains={[
					[list, step("third", "TextRef", { value: "three, a child node" })],
					[list, step("fourth", "BadgeRef", { label: "four", variant: "info" })],
				]}
			/>
		);
	},
};
