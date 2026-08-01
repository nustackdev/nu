import type { Meta, StoryObj } from "@storybook/react-vite";
import { Copy, Edit3, Share2, Trash2 } from "lucide-react";
import { useState } from "react";
import { Button } from "./button";
import {
	DropdownMenu,
	DropdownMenuCheckboxItem,
	DropdownMenuContent,
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

function BasicMenu() {
	const [wrap, setWrap] = useState(true);
	const [density, setDensity] = useState("comfy");
	return (
		<DropdownMenu>
			<DropdownMenuTrigger asChild>
				<Button variant="secondary">Actions</Button>
			</DropdownMenuTrigger>
			<DropdownMenuContent align="start">
				<DropdownMenuLabel>Row</DropdownMenuLabel>
				<DropdownMenuItem>
					<Edit3 />
					Edit
					<DropdownMenuShortcut>E</DropdownMenuShortcut>
				</DropdownMenuItem>
				<DropdownMenuItem>
					<Copy />
					Duplicate
					<DropdownMenuShortcut>D</DropdownMenuShortcut>
				</DropdownMenuItem>
				<DropdownMenuSub>
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
					<DropdownMenuShortcut>Del</DropdownMenuShortcut>
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

const meta: Meta = {
	title: "UI/DropdownMenu",
};

export default meta;
