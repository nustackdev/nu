// Nodes/Disclosure: the containers that open and close over their children,
// as a program draws them. A Collapsible folds a region in place, open and
// closed, with a Card as its body.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Nodes/Disclosure",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

export const Collapsible: Story = {
	render: () => {
		const col = step("disclosure-collapsible", "Column", { gap: 2 });
		const open = step("open", "Collapsible", { title: "Deploy details", open: true });
		const card = step("card", "Card", { title: "web-03", subtitle: "eu-central, 4 vCPU" });
		const closed = step("closed", "Collapsible", { title: "Advanced settings", open: false });
		return (
			<NodeStage
				root="disclosure-collapsible"
				label="one open with a Card inside, one closed"
				chains={[
					[col, open, card, step("status", "BadgeRef", { label: "healthy", variant: "ok" })],
					[col, open, card, step("note", "TextRef", { value: "Last deploy 12 minutes ago." })],
					[col, closed, step("hidden", "TextRef", { value: "Folded away." })],
				]}
			/>
		);
	},
};
