import type { Meta, StoryObj } from "@storybook/react-vite";
import { Calendar, LayoutDashboard, Settings, User } from "lucide-react";
import { useState } from "react";
import { Button } from "./button";
import {
	CommandEmpty,
	CommandGroup,
	CommandInput,
	CommandItem,
	CommandList,
	CommandPalette,
	CommandSeparator,
	CommandShortcut,
	useCommandPaletteHotkey,
} from "./command-palette";

function Sample() {
	const [open, setOpen] = useState(false);
	useCommandPaletteHotkey(setOpen);
	return (
		<>
			<div className="mb-3 text-sm text-text-secondary">
				Press <kbd className="rounded-sm bg-bg-sunken border border-border-subtle px-1.5 py-0.5 font-mono text-xs">⌘K</kbd>
				{" "}or click the button to open.
			</div>
			<Button onClick={() => setOpen(true)}>Open palette</Button>
			<CommandPalette open={open} onOpenChange={setOpen}>
				<CommandInput placeholder="Type a command or search..." />
				<CommandList>
					<CommandEmpty>No results.</CommandEmpty>
					<CommandGroup heading="Navigation">
						<CommandItem>
							<LayoutDashboard />
							Go to dashboard
							<CommandShortcut>G D</CommandShortcut>
						</CommandItem>
						<CommandItem>
							<Calendar />
							Go to schedule
							<CommandShortcut>G S</CommandShortcut>
						</CommandItem>
					</CommandGroup>
					<CommandSeparator />
					<CommandGroup heading="Settings">
						<CommandItem>
							<User />
							Profile
						</CommandItem>
						<CommandItem>
							<Settings />
							Preferences
						</CommandItem>
					</CommandGroup>
					<CommandSeparator />
					<CommandGroup heading="Dangerous">
						<CommandItem variant="danger">Reset workspace</CommandItem>
					</CommandGroup>
				</CommandList>
			</CommandPalette>
		</>
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
	title: "UI/CommandPalette",
};

export default meta;
