// One open overlay per story, for the Overlays page to frame once per theme.
// Hidden from the sidebar: each is a whole document only so its portal lands
// under an <html> that carries the theme.
//
// A highlighted menu row is marked with `data-highlighted` by hand rather than
// by focus: two frames cannot both hold focus, and the mark is what the kit
// styles anyway.

import type { Meta, StoryObj } from "@storybook/react-vite";
import {
	Copy,
	FileText,
	FolderOpen,
	Pencil,
	Plus,
	Search,
	Settings,
	Share2,
	Trash2,
} from "lucide-react";
import type * as React from "react";
import { useEffect, useRef } from "react";
import { Button } from "../../components/ui/button";
import {
	Combobox,
	ComboboxContent,
	ComboboxEmpty,
	ComboboxGroup,
	ComboboxInput,
	ComboboxItem,
	ComboboxList,
	ComboboxTrigger,
} from "../../components/ui/combobox";
import {
	CommandEmpty,
	CommandGroup,
	CommandInput,
	CommandItem,
	CommandList,
	CommandPalette,
	CommandSeparator,
	CommandShortcut,
} from "../../components/ui/command-palette";
import {
	ContextMenu,
	ContextMenuContent,
	ContextMenuItem,
	ContextMenuLabel,
	ContextMenuSeparator,
	ContextMenuShortcut,
	ContextMenuTrigger,
} from "../../components/ui/context-menu";
import { DatePicker } from "../../components/ui/date-picker";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "../../components/ui/dialog";
import {
	DropdownMenu,
	DropdownMenuCheckboxItem,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuShortcut,
	DropdownMenuTrigger,
} from "../../components/ui/dropdown-menu";
import { Input } from "../../components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "../../components/ui/popover";
import {
	Select,
	SelectContent,
	SelectGroup,
	SelectItem,
	SelectLabel,
	SelectSeparator,
	SelectTrigger,
	SelectValue,
} from "../../components/ui/select";
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetFooter,
	SheetHeader,
	SheetTitle,
} from "../../components/ui/sheet";
import { Shortcut } from "../../components/ui/shortcut";
import { Text } from "../../components/ui/text";
import {
	Tooltip,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
} from "../../components/ui/tooltip";

const noop = () => {};

function Pane({ children }: { children: React.ReactNode }) {
	return <div className="flex h-screen items-start gap-6 p-6">{children}</div>;
}

export const Dropdown: StoryObj = {
	render: () => (
		<Pane>
			<DropdownMenu open modal={false}>
				<DropdownMenuTrigger asChild>
					<Button variant="secondary">Actions</Button>
				</DropdownMenuTrigger>
				<DropdownMenuContent align="start" className="w-56">
					<DropdownMenuLabel>File</DropdownMenuLabel>
					<DropdownMenuItem>
						<Pencil />
						Rename
						<DropdownMenuShortcut keys={["F2"]} />
					</DropdownMenuItem>
					<DropdownMenuItem data-highlighted="">
						<Copy />
						Duplicate
						<DropdownMenuShortcut keys={["mod", "D"]} />
					</DropdownMenuItem>
					<DropdownMenuItem disabled>
						<Share2 />
						Share (disabled)
					</DropdownMenuItem>
					<DropdownMenuSeparator />
					<DropdownMenuCheckboxItem checked>Show hidden</DropdownMenuCheckboxItem>
					<DropdownMenuCheckboxItem checked={false}>Wrap lines</DropdownMenuCheckboxItem>
					<DropdownMenuSeparator />
					<DropdownMenuItem variant="danger">
						<Trash2 />
						Delete
						<DropdownMenuShortcut keys={["mod", "Backspace"]} />
					</DropdownMenuItem>
				</DropdownMenuContent>
			</DropdownMenu>
		</Pane>
	),
};

// ContextMenu has no `open` prop: it opens on a right click, so one is sent
// once the trigger is up. Radix also shuts a menu when its window loses focus,
// which happens here as the sibling frames take focus, so this frame's blur
// is swallowed before Radix hears it (this listener is added first).
function ContextPane() {
	const area = useRef<HTMLDivElement>(null);
	useEffect(() => {
		const swallow = (e: FocusEvent) => e.stopImmediatePropagation();
		window.addEventListener("blur", swallow);
		const t = window.setTimeout(() => {
			const el = area.current;
			if (!el) return;
			const r = el.getBoundingClientRect();
			el.dispatchEvent(
				new MouseEvent("contextmenu", {
					bubbles: true,
					cancelable: true,
					clientX: r.left + 24,
					clientY: r.top + 40,
				}),
			);
		}, 100);
		return () => {
			window.removeEventListener("blur", swallow);
			window.clearTimeout(t);
		};
	}, []);
	return (
		<Pane>
			<ContextMenu modal={false}>
				<ContextMenuTrigger asChild>
					<div
						ref={area}
						className="flex h-24 w-56 items-start rounded-md border border-dashed border-border-default p-2"
					>
						<Text size="sm" tone="muted">
							Right click area
						</Text>
					</div>
				</ContextMenuTrigger>
				<ContextMenuContent className="w-56">
					<ContextMenuLabel>notes.md</ContextMenuLabel>
					<ContextMenuItem>
						<FolderOpen />
						Open
					</ContextMenuItem>
					<ContextMenuItem data-highlighted="">
						<Pencil />
						Rename
						<ContextMenuShortcut keys={["F2"]} />
					</ContextMenuItem>
					<ContextMenuSeparator />
					<ContextMenuItem variant="danger">
						<Trash2 />
						Delete
					</ContextMenuItem>
				</ContextMenuContent>
			</ContextMenu>
		</Pane>
	);
}

export const Context: StoryObj = { render: () => <ContextPane /> };

export const Command: StoryObj = {
	render: () => (
		<Pane>
			<CommandPalette open onOpenChange={noop} value="new-file">
				<CommandInput placeholder="Type a command or search..." />
				<CommandList>
					<CommandEmpty>No results.</CommandEmpty>
					<CommandGroup heading="Files">
						<CommandItem value="open-file">
							<FolderOpen />
							Open file
							<CommandShortcut keys={["mod", "O"]} />
						</CommandItem>
						<CommandItem value="new-file">
							<Plus />
							New file
							<CommandShortcut keys={["mod", "N"]} />
						</CommandItem>
						<CommandItem value="recent">
							<FileText />
							Recent files
						</CommandItem>
					</CommandGroup>
					<CommandSeparator />
					<CommandGroup heading="Settings">
						<CommandItem value="settings">
							<Settings />
							Open settings
							<CommandShortcut keys={["mod", ","]} />
						</CommandItem>
						<CommandItem value="clear" variant="danger">
							<Trash2 />
							Clear history
						</CommandItem>
					</CommandGroup>
				</CommandList>
			</CommandPalette>
		</Pane>
	),
};

export const PopoverOpen: StoryObj = {
	name: "Popover",
	render: () => (
		<Pane>
			<Popover open>
				<PopoverTrigger asChild>
					<Button variant="secondary">Filters</Button>
				</PopoverTrigger>
				<PopoverContent align="start">
					<div className="flex flex-col gap-2">
						<Text size="sm" weight="semibold">
							Filter runs
						</Text>
						<Text size="xs" tone="secondary">
							Narrow the list by name or tag.
						</Text>
						<Input size="sm" placeholder="Name contains..." />
						<div className="flex justify-end gap-2">
							<Button size="sm" variant="ghost">
								Reset
							</Button>
							<Button size="sm">Apply</Button>
						</div>
					</div>
				</PopoverContent>
			</Popover>
		</Pane>
	),
};

export const SelectOpen: StoryObj = {
	name: "Select",
	render: () => (
		<Pane>
			<div className="w-56">
				<Select open value="py">
					<SelectTrigger>
						<SelectValue placeholder="Language" />
					</SelectTrigger>
					<SelectContent>
						<SelectGroup>
							<SelectLabel>Languages</SelectLabel>
							<SelectItem value="ts">TypeScript</SelectItem>
							<SelectItem value="py" data-highlighted="">
								Python
							</SelectItem>
							<SelectItem value="rs">Rust</SelectItem>
							<SelectItem value="go" disabled>
								Go (disabled)
							</SelectItem>
						</SelectGroup>
						<SelectSeparator />
						<SelectItem value="none">None</SelectItem>
					</SelectContent>
				</Select>
			</div>
		</Pane>
	),
};

export const ComboboxOpen: StoryObj = {
	name: "Combobox",
	render: () => (
		<Pane>
			<div className="w-60">
				<Combobox open value="nulog">
					<ComboboxTrigger className="w-60">nulog</ComboboxTrigger>
					<ComboboxContent>
						<ComboboxInput placeholder="Search projects..." />
						<ComboboxList>
							<ComboboxEmpty>No match.</ComboboxEmpty>
							<ComboboxGroup heading="Projects">
								<ComboboxItem value="nu">nu</ComboboxItem>
								<ComboboxItem value="nulog">nulog</ComboboxItem>
								<ComboboxItem value="nuspace">nuspace</ComboboxItem>
								<ComboboxItem value="virtuals">virtuals</ComboboxItem>
							</ComboboxGroup>
						</ComboboxList>
					</ComboboxContent>
				</Combobox>
			</div>
		</Pane>
	),
};

// DatePicker keeps its open state to itself, so its trigger is clicked once
// it is up.
function DatePane() {
	const box = useRef<HTMLDivElement>(null);
	useEffect(() => {
		const t = window.setTimeout(() => box.current?.querySelector("button")?.click(), 100);
		return () => window.clearTimeout(t);
	}, []);
	return (
		<Pane>
			<div ref={box} className="w-56">
				<DatePicker defaultValue={new Date(2026, 9, 14)} />
			</div>
		</Pane>
	);
}

export const DateOpen: StoryObj = { name: "Date picker", render: () => <DatePane /> };

export const TooltipOpen: StoryObj = {
	name: "Tooltip",
	render: () => (
		<TooltipProvider>
			<Pane>
				<div className="flex gap-16 pt-10">
					<Tooltip open>
						<TooltipTrigger asChild>
							<Button variant="secondary">Hover me</Button>
						</TooltipTrigger>
						<TooltipContent>Copy the run id</TooltipContent>
					</Tooltip>
					<Tooltip open>
						<TooltipTrigger asChild>
							<Button variant="ghost">
								<Search />
								Search
							</Button>
						</TooltipTrigger>
						<TooltipContent side="bottom">
							<span className="flex items-center gap-2">
								Search everywhere
								<Shortcut keys={["mod", "K"]} />
							</span>
						</TooltipContent>
					</Tooltip>
				</div>
			</Pane>
		</TooltipProvider>
	),
};

export const DialogOpen: StoryObj = {
	name: "Dialog",
	render: () => (
		<Pane>
			<Dialog open>
				<DialogContent size="sm">
					<DialogHeader>
						<DialogTitle>Delete plane?</DialogTitle>
						<DialogDescription>
							This removes the plane and its 12 runs. It cannot be undone.
						</DialogDescription>
					</DialogHeader>
					<DialogFooter>
						<Button variant="ghost">Cancel</Button>
						<Button variant="destructive">Delete</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>
		</Pane>
	),
};

export const SheetOpen: StoryObj = {
	name: "Sheet",
	render: () => (
		<Pane>
			<Sheet open>
				<SheetContent side="right" size="sm">
					<SheetHeader>
						<SheetTitle>Run details</SheetTitle>
						<SheetDescription>Inspect and edit the selected run.</SheetDescription>
					</SheetHeader>
					<Input placeholder="Run name" />
					<SheetFooter>
						<Button variant="ghost">Close</Button>
						<Button>Save</Button>
					</SheetFooter>
				</SheetContent>
			</Sheet>
		</Pane>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Overlay Panes",
	tags: ["!dev", "!autodocs"],
	parameters: { layout: "fullscreen" },
};

export default meta;
