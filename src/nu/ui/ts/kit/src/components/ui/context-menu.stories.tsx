import type { Meta, StoryObj } from "@storybook/react-vite";
import { Copy, Edit3, Trash2 } from "lucide-react";
import {
	ContextMenu,
	ContextMenuContent,
	ContextMenuItem,
	ContextMenuLabel,
	ContextMenuSeparator,
	ContextMenuShortcut,
	ContextMenuTrigger,
} from "./context-menu";

function Sample() {
	return (
		<ContextMenu>
			<ContextMenuTrigger asChild>
				<div className="flex h-32 w-64 items-center justify-center rounded-md border border-dashed border-border-default bg-bg-sunken text-sm text-text-secondary">
					Right-click here
				</div>
			</ContextMenuTrigger>
			<ContextMenuContent>
				<ContextMenuLabel>Row</ContextMenuLabel>
				<ContextMenuItem>
					<Edit3 />
					Rename
					<ContextMenuShortcut>R</ContextMenuShortcut>
				</ContextMenuItem>
				<ContextMenuItem>
					<Copy />
					Duplicate
					<ContextMenuShortcut>D</ContextMenuShortcut>
				</ContextMenuItem>
				<ContextMenuSeparator />
				<ContextMenuItem variant="danger">
					<Trash2 />
					Delete
					<ContextMenuShortcut>Del</ContextMenuShortcut>
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

const meta: Meta = {
	title: "UI/ContextMenu",
};

export default meta;
