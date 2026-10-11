// Nodes/Disclosure: the containers that open and close over their children,
// as a program draws them. A Collapsible folds a region in place, open and
// closed, with a Card as its body. A Sheet slides in from the right over the
// page with a Form as its body; it portals to <body>, so it renders alone in
// a hidden story that the visible one frames once per theme.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { FramePair, NodeSolo, NodeStage, SinkPage, sinkParameters, step } from "./harness";

// The light pin rides each visible story, not the meta, so the hidden pane
// takes the theme its frame asks for.
const meta: Meta = {
	title: "Nodes/Disclosure",
	parameters: { layout: "fullscreen" },
};

export default meta;

type Story = StoryObj;

export const Collapsible: Story = {
	parameters: sinkParameters,
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

// Hidden: the whole document is the frame, so the portal keeps its theme.
export const SheetPane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const col = step("disclosure-sheet", "Column", { gap: 3 });
		const sheet = step("inspector", "Sheet", {
			title: "Edit host",
			open: true,
			side: "right",
			size: "sm",
		});
		const form = step("form", "Form", { gap: 4 });
		return (
			<NodeSolo
				root="disclosure-sheet"
				chains={[
					[col, step("heading", "HeadingRef", { label: "Hosts" })],
					[
						col,
						step("intro", "TextRef", { value: "The page under the sheet, dimmed by the scrim." }),
					],
					[col, sheet, step("hint", "TextRef", { value: "Changes apply on the next deploy." })],
					[
						col,
						sheet,
						form,
						step("name", "InputRef", { label: "Host name", placeholder: "web-03" }),
					],
					[
						col,
						sheet,
						form,
						step("region", "InputRef", { label: "Region", placeholder: "eu-central" }),
					],
					[col, sheet, form, step("save", "ButtonRef", { label: "Save changes" })],
				]}
			/>
		);
	},
};

export const Sheet: Story = {
	parameters: sinkParameters,
	render: () => (
		<SinkPage
			title="Sheet"
			description="Open on the right with a Form as its body, one frame per theme so the portal keeps its theme."
		>
			<div className="py-6">
				<FramePair storyId="nodes-disclosure--sheet-pane" label="Sheet, right, sm" height={460} />
			</div>
		</SinkPage>
	),
};
