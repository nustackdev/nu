import type { Meta, StoryObj } from "@storybook/react-vite";
import { Copy, Edit3, Share2, Trash2 } from "lucide-react";
import {
	ContextMenu,
	ContextMenuContent,
	ContextMenuItem,
	ContextMenuLabel,
	ContextMenuSeparator,
	ContextMenuShortcut,
	ContextMenuSub,
	ContextMenuSubContent,
	ContextMenuSubTrigger,
	ContextMenuTrigger,
} from "./context-menu";

function Sample() {
	return (
		<ContextMenu>
			<ContextMenuTrigger asChild>
				<div className="flex h-32 w-64 items-center justify-center rounded-md border border-dashed border-border-default bg-bg-sunken text-sm text-text-secondary">
					Right-click or long-press here
				</div>
			</ContextMenuTrigger>
			<ContextMenuContent>
				<ContextMenuLabel>Row</ContextMenuLabel>
				<ContextMenuItem>
					<Edit3 />
					Rename
					<ContextMenuShortcut keys={["mod", "R"]} />
				</ContextMenuItem>
				<ContextMenuItem>
					<Copy />
					Duplicate
					<ContextMenuShortcut keys={["mod", "D"]} />
				</ContextMenuItem>
				<ContextMenuSub>
					<ContextMenuSubTrigger>
						<Share2 />
						Share
					</ContextMenuSubTrigger>
					<ContextMenuSubContent>
						<ContextMenuItem>Copy link</ContextMenuItem>
						<ContextMenuItem>Copy embed</ContextMenuItem>
					</ContextMenuSubContent>
				</ContextMenuSub>
				<ContextMenuSeparator />
				<ContextMenuItem variant="danger">
					<Trash2 />
					Delete
					<ContextMenuShortcut keys={["delete"]} />
				</ContextMenuItem>
			</ContextMenuContent>
		</ContextMenu>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Sample />
			</div>
	),
};

export const Matrix = Default;

// Opened at load by a right-click on the region, which a phone's long-press
// stands in for: on touch it is a bottom sheet, on desktop the menu at the
// pointer.
export const Open: StoryObj = {
	render: Default.render,
	play: async ({ canvasElement }) => {
		const region = canvasElement.querySelector<HTMLElement>('[data-slot="context-menu-trigger"]');
		if (!region) return;
		const box = region.getBoundingClientRect();
		region.dispatchEvent(
			new MouseEvent("contextmenu", {
				bubbles: true,
				cancelable: true,
				button: 2,
				clientX: box.left + box.width / 2,
				clientY: box.top + box.height / 2,
			}),
		);
	},
};

const meta: Meta = {
	title: "UI/ContextMenu",
};

export default meta;
