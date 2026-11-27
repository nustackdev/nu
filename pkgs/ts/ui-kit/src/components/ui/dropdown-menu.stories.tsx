import type { Meta, StoryObj } from "@storybook/react-vite";
import { Copy, Edit3, Share2, Trash2 } from "lucide-react";
import { useState } from "react";
import { Button } from "./button";
import {
	DropdownMenu,
	DropdownMenuCheckboxItem,
	DropdownMenuContent,
	DropdownMenuDetail,
	DropdownMenuDetails,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuSeparator,
	DropdownMenuShortcut,
	DropdownMenuSub,
	DropdownMenuSubContent,
	DropdownMenuSubTrigger,
	DropdownMenuTrigger,
} from "./dropdown-menu";

function BasicMenu({ open, subOpen }: { open?: boolean; subOpen?: boolean }) {
	const [wrap, setWrap] = useState(true);
	const [density, setDensity] = useState("comfy");
	return (
		<DropdownMenu defaultOpen={open}>
			<DropdownMenuTrigger asChild>
				<Button variant="secondary">Actions</Button>
			</DropdownMenuTrigger>
			<DropdownMenuContent align="start">
				<DropdownMenuLabel>Row</DropdownMenuLabel>
				<DropdownMenuItem>
					<Edit3 />
					Edit
					<DropdownMenuShortcut keys={["mod", "E"]} />
				</DropdownMenuItem>
				<DropdownMenuItem>
					<Copy />
					Duplicate
					<DropdownMenuShortcut keys={["mod", "D"]} />
				</DropdownMenuItem>
				<DropdownMenuSub defaultOpen={subOpen}>
					<DropdownMenuSubTrigger>
						<Share2 />
						Share
					</DropdownMenuSubTrigger>
					<DropdownMenuSubContent>
						<DropdownMenuItem>Copy link</DropdownMenuItem>
						<DropdownMenuItem>Copy embed</DropdownMenuItem>
					</DropdownMenuSubContent>
				</DropdownMenuSub>
				<DropdownMenuSeparator />
				<DropdownMenuLabel>View</DropdownMenuLabel>
				<DropdownMenuCheckboxItem
					checked={wrap}
					onCheckedChange={(v) => setWrap(v === true)}
				>
					Wrap long values
				</DropdownMenuCheckboxItem>
				<DropdownMenuSeparator />
				<DropdownMenuLabel>Density</DropdownMenuLabel>
				<DropdownMenuRadioGroup value={density} onValueChange={setDensity}>
					<DropdownMenuRadioItem value="compact">Compact</DropdownMenuRadioItem>
					<DropdownMenuRadioItem value="default">Default</DropdownMenuRadioItem>
					<DropdownMenuRadioItem value="comfy">Comfy</DropdownMenuRadioItem>
				</DropdownMenuRadioGroup>
				<DropdownMenuSeparator />
				<DropdownMenuItem variant="danger">
					<Trash2 />
					Delete
					<DropdownMenuShortcut keys={["delete"]} />
				</DropdownMenuItem>
			</DropdownMenuContent>
		</DropdownMenu>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<BasicMenu />
			</div>
	),
};

/** Facts above the actions: what the menu acts on, read-only. */
export const WithDetails: StoryObj = {
	render: () => (
		<div className="p-8">
			<DropdownMenu>
				<DropdownMenuTrigger asChild>
					<Button variant="secondary">Cell</Button>
				</DropdownMenuTrigger>
				<DropdownMenuContent align="start" className="w-64">
					<DropdownMenuLabel>Text</DropdownMenuLabel>
					<DropdownMenuDetails>
						<DropdownMenuDetail label="Id" mono>
							a1b2c3d4
						</DropdownMenuDetail>
						<DropdownMenuDetail label="Version" mono>
							v7
						</DropdownMenuDetail>
						<DropdownMenuDetail label="Ran" mono tone="warn">
							v5
						</DropdownMenuDetail>
						<DropdownMenuDetail label="Error" tone="danger" wrap>
							ZeroDivisionError: division by zero
						</DropdownMenuDetail>
					</DropdownMenuDetails>
					<DropdownMenuSeparator />
					<DropdownMenuItem>
						<Edit3 />
						Edit
					</DropdownMenuItem>
					<DropdownMenuItem variant="danger">
						<Trash2 />
						Delete
					</DropdownMenuItem>
				</DropdownMenuContent>
			</DropdownMenu>
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-4">
				<div className="font-mono text-xs uppercase tracking-widest text-text-muted">
					all pieces (item, checkbox item, radio group, submenu, separator, label, danger)
				</div>
				<BasicMenu />
			</div>
	),
};

// Opened at load: in touch mode (a phone, or the Touch toolbar) it is a
// bottom sheet of 44px rows with no shortcut hints, on desktop the anchored
// menu.
export const Open: StoryObj = {
	render: () => (
		<div className="p-8">
			<BasicMenu open />
		</div>
	),
};

// The submenu open too: on touch it expands in place under its row.
export const OpenSubmenu: StoryObj = {
	render: () => (
		<div className="p-8">
			<BasicMenu open subOpen />
		</div>
	),
};

// Facts above the actions, opened: on touch they line up with the rows.
export const OpenWithDetails: StoryObj = {
	render: () => (
		<div className="p-8">
			<DropdownMenu defaultOpen>
				<DropdownMenuTrigger asChild>
					<Button variant="secondary">Cell</Button>
				</DropdownMenuTrigger>
				<DropdownMenuContent align="start" className="w-64">
					<DropdownMenuLabel>Text</DropdownMenuLabel>
					<DropdownMenuDetails>
						<DropdownMenuDetail label="Id" mono>
							a1b2c3d4
						</DropdownMenuDetail>
						<DropdownMenuDetail label="Error" tone="danger" wrap>
							ZeroDivisionError: division by zero
						</DropdownMenuDetail>
					</DropdownMenuDetails>
					<DropdownMenuSeparator />
					<DropdownMenuItem>
						<Edit3 />
						Edit
					</DropdownMenuItem>
					<DropdownMenuItem disabled>
						<Copy />
						Duplicate
					</DropdownMenuItem>
					<DropdownMenuItem variant="danger">
						<Trash2 />
						Delete
					</DropdownMenuItem>
				</DropdownMenuContent>
			</DropdownMenu>
		</div>
	),
};

const meta: Meta = {
	title: "UI/DropdownMenu",
};

export default meta;
