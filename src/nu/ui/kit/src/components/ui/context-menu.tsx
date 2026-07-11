// ContextMenu primitive: right-click/long-press menu on a region.
// Design refs:
//   primitives.md    §ContextMenu (mirrors DropdownMenu shape)
//   motion.md        §3 ContextMenu (`duration-base` fade+scale, no y-shift)
//   a11y.md          §3 ContextMenu (Menu key / Shift+F10, then DropdownMenu keys)
//
// Item visual contract matches DropdownMenu exactly, so we reuse
// menuItemClasses / menuItemDangerClasses from there. Content uses fade+scale
// motion (anchor is the cursor, y-shift would drift away from it).

import { ContextMenu as ContextMenuPrimitive } from "radix-ui";
import { Check, ChevronRight, Circle } from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";
import {
	menuItemClasses,
	menuItemDangerClasses,
} from "./dropdown-menu";

const contextMenuContentClasses = [
	"z-50 min-w-[10rem] overflow-hidden p-1",
	"bg-bg-elevated text-text-primary border border-border-subtle rounded-md shadow-lg",
	"data-[state=open]:animate-in data-[state=closed]:animate-out",
	"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
	"data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95",
	"data-[state=open]:duration-base data-[state=closed]:duration-base",
	"data-[state=open]:ease-out data-[state=closed]:ease-in",
].join(" ");

function ContextMenu({
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Root>) {
	return <ContextMenuPrimitive.Root data-slot="context-menu" {...props} />;
}

function ContextMenuTrigger({
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Trigger>) {
	return (
		<ContextMenuPrimitive.Trigger data-slot="context-menu-trigger" {...props} />
	);
}

function ContextMenuGroup({
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Group>) {
	return (
		<ContextMenuPrimitive.Group data-slot="context-menu-group" {...props} />
	);
}

function ContextMenuRadioGroup({
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.RadioGroup>) {
	return (
		<ContextMenuPrimitive.RadioGroup
			data-slot="context-menu-radio-group"
			{...props}
		/>
	);
}

function ContextMenuSub({
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Sub>) {
	return <ContextMenuPrimitive.Sub data-slot="context-menu-sub" {...props} />;
}

function ContextMenuContent({
	className,
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Content>) {
	return (
		<ContextMenuPrimitive.Portal>
			<ContextMenuPrimitive.Content
				data-slot="context-menu-content"
				className={cn(contextMenuContentClasses, className)}
				{...props}
			/>
		</ContextMenuPrimitive.Portal>
	);
}

interface ContextMenuItemProps
	extends React.ComponentProps<typeof ContextMenuPrimitive.Item> {
	variant?: "default" | "danger";
	inset?: boolean;
}

function ContextMenuItem({
	className,
	variant = "default",
	inset,
	...props
}: ContextMenuItemProps) {
	return (
		<ContextMenuPrimitive.Item
			data-slot="context-menu-item"
			data-variant={variant}
			className={cn(
				menuItemClasses,
				variant === "danger" && menuItemDangerClasses,
				inset && "pl-8",
				className,
			)}
			{...props}
		/>
	);
}

function ContextMenuCheckboxItem({
	className,
	children,
	checked,
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.CheckboxItem>) {
	return (
		<ContextMenuPrimitive.CheckboxItem
			data-slot="context-menu-checkbox-item"
			checked={checked}
			className={cn(menuItemClasses, "pl-8", className)}
			{...props}
		>
			<span className="absolute left-2 flex size-4 items-center justify-center">
				<ContextMenuPrimitive.ItemIndicator>
					<Check className="size-3.5 text-accent" />
				</ContextMenuPrimitive.ItemIndicator>
			</span>
			{children}
		</ContextMenuPrimitive.CheckboxItem>
	);
}

function ContextMenuRadioItem({
	className,
	children,
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.RadioItem>) {
	return (
		<ContextMenuPrimitive.RadioItem
			data-slot="context-menu-radio-item"
			className={cn(menuItemClasses, "pl-8", className)}
			{...props}
		>
			<span className="absolute left-2 flex size-4 items-center justify-center">
				<ContextMenuPrimitive.ItemIndicator>
					<Circle className="size-2 fill-accent text-accent" />
				</ContextMenuPrimitive.ItemIndicator>
			</span>
			{children}
		</ContextMenuPrimitive.RadioItem>
	);
}

interface ContextMenuLabelProps
	extends React.ComponentProps<typeof ContextMenuPrimitive.Label> {
	inset?: boolean;
}

function ContextMenuLabel({
	className,
	inset,
	...props
}: ContextMenuLabelProps) {
	return (
		<ContextMenuPrimitive.Label
			data-slot="context-menu-label"
			className={cn(
				"px-2 py-1.5 text-xs font-medium text-text-secondary",
				inset && "pl-8",
				className,
			)}
			{...props}
		/>
	);
}

function ContextMenuSeparator({
	className,
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Separator>) {
	return (
		<ContextMenuPrimitive.Separator
			data-slot="context-menu-separator"
			className={cn("-mx-1 my-1 h-px bg-border-subtle", className)}
			{...props}
		/>
	);
}

interface ContextMenuSubTriggerProps
	extends React.ComponentProps<typeof ContextMenuPrimitive.SubTrigger> {
	inset?: boolean;
}

function ContextMenuSubTrigger({
	className,
	inset,
	children,
	...props
}: ContextMenuSubTriggerProps) {
	return (
		<ContextMenuPrimitive.SubTrigger
			data-slot="context-menu-sub-trigger"
			className={cn(
				menuItemClasses,
				"data-[state=open]:bg-accent-wash",
				inset && "pl-8",
				className,
			)}
			{...props}
		>
			{children}
			<ChevronRight className="ml-auto size-4 text-text-secondary" />
		</ContextMenuPrimitive.SubTrigger>
	);
}

function ContextMenuSubContent({
	className,
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.SubContent>) {
	return (
		<ContextMenuPrimitive.SubContent
			data-slot="context-menu-sub-content"
			className={cn(contextMenuContentClasses, className)}
			{...props}
		/>
	);
}

function ContextMenuShortcut({
	className,
	...props
}: React.HTMLAttributes<HTMLSpanElement>) {
	return (
		<span
			data-slot="context-menu-shortcut"
			className={cn(
				"ml-auto font-mono text-xs tracking-wide text-text-muted",
				className,
			)}
			{...props}
		/>
	);
}

export {
	ContextMenu,
	ContextMenuTrigger,
	ContextMenuContent,
	ContextMenuItem,
	ContextMenuCheckboxItem,
	ContextMenuRadioGroup,
	ContextMenuRadioItem,
	ContextMenuLabel,
	ContextMenuSeparator,
	ContextMenuGroup,
	ContextMenuSub,
	ContextMenuSubTrigger,
	ContextMenuSubContent,
	ContextMenuShortcut,
};
