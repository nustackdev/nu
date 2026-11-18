// Refs/Disclosure: the containers that open and close over their children,
// as a program draws them. A Collapsible folds a region in place, open and
// closed, with a Card as its body. A Sheet slides in from the right over the
// page with a Form as its body, once with a string title and once with a Row
// at `header` in its place. A Modal headed by a Row, and a Popover whose
// trigger is an avatar and a name in one button and whose panel is headed by
// a Row. The overlays portal to <body>, so each renders alone in a hidden
// story that the visible one frames once per theme.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { FramePair, NodeSolo, NodeStage, SinkPage, sinkParameters, step } from "./harness";

// The light pin rides each visible story, not the meta, so the hidden pane
// takes the theme its frame asks for.
const meta: Meta = {
	title: "Refs/Disclosure",
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
			width: 320,
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

// Hidden: a sheet headed by a Row (status dot, host name cut to one line, a
// badge) in place of its title, the close button kept beside it.
export const SheetHeaderPane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const col = step("disclosure-sheet-header", "Column", { gap: 3 });
		const sheet = step("inspector", "Sheet", { open: true, side: "right", width: 320 });
		const head = step("header", "Row", { gap: 2, grow: { name: 1 } });
		return (
			<NodeSolo
				root="disclosure-sheet-header"
				chains={[
					[col, step("heading", "HeadingRef", { label: "Hosts" })],
					[col, sheet, head, step("dot", "StatusDotRef", { tone: "ok" })],
					[
						col,
						sheet,
						head,
						step("name", "TextRef", {
							value: "web-03.eu-central.cluster.internal",
							weight: "semibold",
							lines: 1,
						}),
					],
					[col, sheet, head, step("role", "BadgeRef", { label: "primary" })],
					[col, sheet, step("hint", "TextRef", { value: "4 vCPU, 16 GB, up 12 days." })],
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
			description="Open on the right with a Form as its body, then with a Row at `header` in place of the title. One frame per theme so the portal keeps its theme."
		>
			<div className="flex flex-col gap-6 py-6">
				<FramePair storyId="refs-disclosure--sheet-pane" label="Sheet, right, sm" height={460} />
				<FramePair
					storyId="refs-disclosure--sheet-header-pane"
					label="Sheet, header Row in place of the title"
					height={320}
				/>
			</div>
		</SinkPage>
	),
};

// Hidden: a modal headed by a Row (icon, name, badge), the close button kept.
export const ModalHeaderPane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const col = step("disclosure-modal-header", "Column", { gap: 3 });
		const modal = step("confirm", "Modal", { open: true, width: 420 });
		const head = step("header", "Row", { gap: 2 });
		return (
			<NodeSolo
				root="disclosure-modal-header"
				chains={[
					[col, step("heading", "HeadingRef", { label: "Deploys" })],
					[col, modal, head, step("icon", "IconRef", { name: "rocket", tone: "accent" })],
					[
						col,
						modal,
						head,
						step("title", "TextRef", { value: "Deploy web-03", size: "lg", weight: "semibold" }),
					],
					[col, modal, head, step("env", "BadgeRef", { label: "prod", variant: "warn" })],
					[col, modal, step("note", "TextRef", { value: "Rolls out to 4 hosts, one at a time." })],
					[col, modal, step("go", "ButtonRef", { label: "Deploy" })],
				]}
			/>
		);
	},
};

export const Modal: Story = {
	parameters: sinkParameters,
	render: () => (
		<SinkPage
			title="Modal"
			description="A Row at `header` in place of the title, the close button kept; the dialog is named by it."
		>
			<div className="py-6">
				<FramePair
					storyId="refs-disclosure--modal-header-pane"
					label="Modal, header Row"
					height={340}
				/>
			</div>
		</SinkPage>
	),
};

// Hidden: an open popover whose trigger is an avatar and a name in one button,
// and whose panel is headed by a Row in place of its title.
export const PopoverHeaderPane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const row = step("disclosure-popover-header", "Row", { gap: 3, justify: "end" });
		const pop = step("account", "Popover", {
			tooltip: "Account",
			variant: "ghost",
			open: true,
			width: 260,
		});
		const trigger = step("trigger", "Row", { gap: 2 });
		const head = step("header", "Row", { gap: 2 });
		return (
			<NodeSolo
				root="disclosure-popover-header"
				chains={[
					[row, pop, trigger, step("avatar", "AvatarRef", { name: "Ada Lovelace", size: "sm" })],
					[row, pop, trigger, step("name", "TextRef", { value: "Ada", size: "sm" })],
					[row, pop, head, step("who", "TextRef", { value: "ada@example.com", lines: 1 })],
					[row, pop, head, step("plan", "BadgeRef", { label: "pro" })],
					[row, pop, step("settings", "ButtonRef", { label: "Settings", variant: "ghost" })],
					[row, pop, step("out", "ButtonRef", { label: "Sign out", variant: "ghost" })],
				]}
			/>
		);
	},
};

export const Popover: Story = {
	parameters: sinkParameters,
	render: () => (
		<SinkPage
			title="Popover"
			description="A Row at `trigger` drawn inside one button, and a Row at `header` heading the panel."
		>
			<div className="py-6">
				<FramePair
					storyId="refs-disclosure--popover-header-pane"
					label="Popover, trigger and header Rows"
					height={300}
				/>
			</div>
		</SinkPage>
	),
};
