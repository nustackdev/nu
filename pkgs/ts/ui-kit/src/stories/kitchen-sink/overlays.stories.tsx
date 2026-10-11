// Kitchen sink: menus and overlays, open, light and dark side by side.
//
// Every overlay here portals to <body>, out of reach of a `.dark` column, so
// each one renders alone in a frame per theme (overlay-panes.stories.tsx).
// A frame is its own viewport: overlays never pile on each other, and modal
// ones (Dialog, Sheet, CommandPalette) dim only their own cell.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { Text } from "../../components/ui/text";
import { FramePair, SinkPage, sinkParameters } from "./frame";

const PANES = [
	{ id: "dropdown", label: "DropdownMenu", height: 340 },
	{ id: "context", label: "ContextMenu", height: 260 },
	{ id: "command", label: "CommandPalette", height: 460 },
	{ id: "popover-open", label: "Popover", height: 260 },
	{ id: "select-open", label: "Select", height: 300 },
	{ id: "combobox-open", label: "Combobox", height: 300 },
	{ id: "date-open", label: "DatePicker", height: 400 },
	{ id: "tooltip-open", label: "Tooltip", height: 160 },
	{ id: "dialog-open", label: "Dialog", height: 320 },
	{ id: "sheet-open", label: "Sheet", height: 360 },
] as const;

export const Default: StoryObj = {
	name: "Overlays",
	render: () => (
		<SinkPage
			title="Overlays"
			description="Menus, popovers and dialogs rendered open. Each sits in its own frame per theme so portals keep their theme."
		>
			<div className="grid grid-cols-2 px-8 pt-6">
				<Text size="xs" tone="muted" mono className="uppercase tracking-widest">
					light
				</Text>
				<Text size="xs" tone="muted" mono className="uppercase tracking-widest">
					dark
				</Text>
			</div>
			<div className="flex flex-col gap-8 py-6">
				{PANES.map((pane) => (
					<FramePair
						key={pane.id}
						storyId={`kitchen-sink-overlay-panes--${pane.id}`}
						label={pane.label}
						height={pane.height}
					/>
				))}
			</div>
		</SinkPage>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Overlays",
	parameters: sinkParameters,
};

export default meta;
