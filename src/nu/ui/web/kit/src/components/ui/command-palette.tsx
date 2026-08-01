// CommandPalette primitive: global cmd+k command runner.
// Design refs:
//   primitives.md    §CommandPalette (parts, motion, mod+k contract)
//   palette.md       §2.1 backgrounds, §2.4 accent-wash (selection tint)
//   space-radius.md  input row 40, item row 32
//   motion.md        §3 CommandPalette (`duration-base` fade+scale on dialog)
//   a11y.md          §3 CommandPalette (Esc close, arrows navigate)
//
// Composition: kit Dialog wrapper + `cmdk` <Command.*> parts. Dialog handles
// focus trap + backdrop + Esc; cmdk handles filter, item roving, typeahead.
// Consumer wires the mod+k hotkey via the exported `useCommandPaletteHotkey`
// helper (a11y.md keeps global shortcuts consumer-owned).

import { Command as CommandPrimitive } from "cmdk";
import { Dialog as DialogPrimitive } from "radix-ui";
import { Search } from "lucide-react";
import * as React from "react";

import { cn } from "../../lib/utils";

interface CommandPaletteProps
	extends React.ComponentProps<typeof CommandPrimitive> {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	// Accessible label read by screen readers; not shown visually.
	label?: string;
}

function CommandPalette({
	open,
	onOpenChange,
	label = "Command palette",
	className,
	children,
	...props
}: CommandPaletteProps) {
	return (
		<DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
			<DialogPrimitive.Portal>
				<DialogPrimitive.Overlay
					data-slot="command-palette-overlay"
					className={cn(
						"fixed inset-0 z-50 bg-bg-overlay",
						"data-[state=open]:animate-in data-[state=closed]:animate-out",
						"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
						"data-[state=open]:duration-base data-[state=closed]:duration-base",
						"data-[state=open]:ease-out data-[state=closed]:ease-in",
					)}
				/>
				<DialogPrimitive.Content
					data-slot="command-palette-content"
					className={cn(
						"fixed left-1/2 top-[20%] z-50 w-full max-w-lg -translate-x-1/2",
						"bg-bg-elevated text-text-primary border border-border-default rounded-lg shadow-lg overflow-hidden",
						"data-[state=open]:animate-in data-[state=closed]:animate-out",
						"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
						"data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95",
						"data-[state=open]:duration-base data-[state=closed]:duration-base",
						"data-[state=open]:ease-out data-[state=closed]:ease-in",
					)}
				>
					<DialogPrimitive.Title className="sr-only">
						{label}
					</DialogPrimitive.Title>
					<DialogPrimitive.Description className="sr-only">
						Type to search commands.
					</DialogPrimitive.Description>
					<CommandPrimitive
						data-slot="command-palette"
						className={cn(
							"flex h-full w-full flex-col",
							"[&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-1 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-text-secondary",
							className,
						)}
						{...props}
					>
						{children}
					</CommandPrimitive>
				</DialogPrimitive.Content>
			</DialogPrimitive.Portal>
		</DialogPrimitive.Root>
	);
}

function CommandInput({
	className,
	...props
}: React.ComponentProps<typeof CommandPrimitive.Input>) {
	return (
		<div
			data-slot="command-palette-input-wrapper"
			className="flex items-center gap-2 border-b border-border-subtle px-3 h-10"
		>
			<Search className="size-4 shrink-0 text-text-secondary" />
			<CommandPrimitive.Input
				data-slot="command-palette-input"
				className={cn(
					"flex h-10 w-full rounded-md bg-transparent text-sm text-text-primary outline-hidden",
					"placeholder:text-text-muted",
					"disabled:cursor-not-allowed disabled:opacity-50",
					className,
				)}
				{...props}
			/>
		</div>
	);
}

function CommandList({
	className,
	...props
}: React.ComponentProps<typeof CommandPrimitive.List>) {
	return (
		<CommandPrimitive.List
			data-slot="command-palette-list"
			className={cn(
				"max-h-80 overflow-y-auto overflow-x-hidden p-1",
				className,
			)}
			{...props}
		/>
	);
}

function CommandEmpty({
	className,
	...props
}: React.ComponentProps<typeof CommandPrimitive.Empty>) {
	return (
		<CommandPrimitive.Empty
			data-slot="command-palette-empty"
			className={cn(
				"py-6 text-center text-sm text-text-muted",
				className,
			)}
			{...props}
		/>
	);
}

function CommandGroup({
	className,
	...props
}: React.ComponentProps<typeof CommandPrimitive.Group>) {
	return (
		<CommandPrimitive.Group
			data-slot="command-palette-group"
			className={cn(
				"overflow-hidden p-1 text-text-primary",
				className,
			)}
			{...props}
		/>
	);
}

function CommandSeparator({
	className,
	...props
}: React.ComponentProps<typeof CommandPrimitive.Separator>) {
	return (
		<CommandPrimitive.Separator
			data-slot="command-palette-separator"
			className={cn("-mx-1 my-1 h-px bg-border-subtle", className)}
			{...props}
		/>
	);
}

interface CommandItemProps
	extends React.ComponentProps<typeof CommandPrimitive.Item> {
	variant?: "default" | "danger";
}

function CommandItem({
	className,
	variant = "default",
	...props
}: CommandItemProps) {
	return (
		<CommandPrimitive.Item
			data-slot="command-palette-item"
			data-variant={variant}
			className={cn(
				"relative flex cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-2",
				"text-sm text-text-primary outline-hidden",
				"data-[selected=true]:bg-accent-wash",
				"data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
				"[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg]:size-4 [&_svg]:text-text-secondary",
				"data-[selected=true]:[&_svg]:text-text-primary",
				variant === "danger" && [
					"text-status-danger",
					"data-[selected=true]:bg-status-danger-wash data-[selected=true]:text-status-danger",
					"[&_svg]:text-status-danger",
					"data-[selected=true]:[&_svg]:text-status-danger",
				].join(" "),
				className,
			)}
			{...props}
		/>
	);
}

function CommandShortcut({
	className,
	...props
}: React.HTMLAttributes<HTMLSpanElement>) {
	return (
		<span
			data-slot="command-palette-shortcut"
			className={cn(
				"ml-auto font-mono text-xs tracking-wide text-text-muted",
				className,
			)}
			{...props}
		/>
	);
}

// Consumer wires mod+k -> setOpen(o => !o). Runs on window keydown, cleans up
// on unmount. Not automatic: multiple palettes / test envs shouldn't fight
// for the same combo. See a11y.md §3 (global shortcut ownership rule).
function useCommandPaletteHotkey(
	setOpen: React.Dispatch<React.SetStateAction<boolean>>,
) {
	React.useEffect(() => {
		function handler(event: KeyboardEvent) {
			if (event.key === "k" && (event.metaKey || event.ctrlKey)) {
				event.preventDefault();
				setOpen((o) => !o);
			}
		}
		window.addEventListener("keydown", handler);
		return () => window.removeEventListener("keydown", handler);
	}, [setOpen]);
}

export {
	CommandPalette,
	CommandInput,
	CommandList,
	CommandEmpty,
	CommandGroup,
	CommandItem,
	CommandSeparator,
	CommandShortcut,
	useCommandPaletteHotkey,
};
