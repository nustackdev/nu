// DropdownMenu primitive: vertical command menu anchored to a trigger.
// Design refs:
//   primitives.md    §DropdownMenu (parts, item variants, motion)
//   palette.md       §2.1 backgrounds, §2.4 accent (accent-wash for hover)
//   space-radius.md  item row 28
//   motion.md        §3 DropdownMenu (`duration-base` fade + y-shift)
//   a11y.md          §3 DropdownMenu (arrows, submenu, typeahead)

import { DropdownMenu as DropdownMenuPrimitive } from "radix-ui";
import { Check, ChevronRight, Circle } from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";

// Shared item recipe: kept here so ContextMenu can borrow it verbatim.
const menuItemClasses = [
	"relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5",
	"text-sm text-text-primary outline-hidden",
	"transition-colors duration-fast ease-out",
	"data-[highlighted]:bg-accent-wash",
	"data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
	"[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg]:size-4 [&_svg]:text-text-secondary",
	"data-[highlighted]:[&_svg]:text-text-primary",
].join(" ");

const menuItemDangerClasses = [
	"text-status-danger",
	"data-[highlighted]:bg-status-danger-wash data-[highlighted]:text-status-danger",
	"[&_svg]:text-status-danger",
	"data-[highlighted]:[&_svg]:text-status-danger",
].join(" ");

const menuContentClasses = [
	"z-50 min-w-[10rem] overflow-hidden p-1",
	"bg-bg-elevated text-text-primary border border-border-subtle rounded-md shadow-lg",
	"data-[state=open]:animate-in data-[state=closed]:animate-out",
	"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
	"data-[state=open]:duration-base data-[state=closed]:duration-base",
	"data-[state=open]:ease-out data-[state=closed]:ease-in",
	"data-[side=top]:data-[state=open]:slide-in-from-bottom-1",
	"data-[side=bottom]:data-[state=open]:slide-in-from-top-1",
	"data-[side=left]:data-[state=open]:slide-in-from-right-1",
	"data-[side=right]:data-[state=open]:slide-in-from-left-1",
].join(" ");

function DropdownMenu({
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Root>) {
	return <DropdownMenuPrimitive.Root data-slot="dropdown-menu" {...props} />;
}

function DropdownMenuTrigger({
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Trigger>) {
	return (
		<DropdownMenuPrimitive.Trigger
			data-slot="dropdown-menu-trigger"
			{...props}
		/>
	);
}

function DropdownMenuGroup({
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Group>) {
	return (
		<DropdownMenuPrimitive.Group data-slot="dropdown-menu-group" {...props} />
	);
}

function DropdownMenuRadioGroup({
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.RadioGroup>) {
	return (
		<DropdownMenuPrimitive.RadioGroup
			data-slot="dropdown-menu-radio-group"
			{...props}
		/>
	);
}

function DropdownMenuSub({
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Sub>) {
	return <DropdownMenuPrimitive.Sub data-slot="dropdown-menu-sub" {...props} />;
}

function DropdownMenuContent({
	className,
	sideOffset = 4,
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Content>) {
	return (
		<DropdownMenuPrimitive.Portal>
			<DropdownMenuPrimitive.Content
				data-slot="dropdown-menu-content"
				sideOffset={sideOffset}
				className={cn(menuContentClasses, className)}
				{...props}
			/>
		</DropdownMenuPrimitive.Portal>
	);
}

interface DropdownMenuItemProps
	extends React.ComponentProps<typeof DropdownMenuPrimitive.Item> {
	variant?: "default" | "danger";
	inset?: boolean;
}

function DropdownMenuItem({
	className,
	variant = "default",
	inset,
	...props
}: DropdownMenuItemProps) {
	return (
		<DropdownMenuPrimitive.Item
			data-slot="dropdown-menu-item"
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

function DropdownMenuCheckboxItem({
	className,
	children,
	checked,
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.CheckboxItem>) {
	return (
		<DropdownMenuPrimitive.CheckboxItem
			data-slot="dropdown-menu-checkbox-item"
			checked={checked}
			className={cn(menuItemClasses, "pl-8", className)}
			{...props}
		>
			<span className="absolute left-2 flex size-4 items-center justify-center">
				<DropdownMenuPrimitive.ItemIndicator>
					<Check className="size-3.5 text-accent" />
				</DropdownMenuPrimitive.ItemIndicator>
			</span>
			{children}
		</DropdownMenuPrimitive.CheckboxItem>
	);
}

function DropdownMenuRadioItem({
	className,
	children,
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.RadioItem>) {
	return (
		<DropdownMenuPrimitive.RadioItem
			data-slot="dropdown-menu-radio-item"
			className={cn(menuItemClasses, "pl-8", className)}
			{...props}
		>
			<span className="absolute left-2 flex size-4 items-center justify-center">
				<DropdownMenuPrimitive.ItemIndicator>
					<Circle className="size-2 fill-accent text-accent" />
				</DropdownMenuPrimitive.ItemIndicator>
			</span>
			{children}
		</DropdownMenuPrimitive.RadioItem>
	);
}

interface DropdownMenuLabelProps
	extends React.ComponentProps<typeof DropdownMenuPrimitive.Label> {
	inset?: boolean;
}

function DropdownMenuLabel({
	className,
	inset,
	...props
}: DropdownMenuLabelProps) {
	return (
		<DropdownMenuPrimitive.Label
			data-slot="dropdown-menu-label"
			className={cn(
				"px-2 py-1.5 text-xs font-medium text-text-secondary",
				inset && "pl-8",
				className,
			)}
			{...props}
		/>
	);
}

function DropdownMenuSeparator({
	className,
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Separator>) {
	return (
		<DropdownMenuPrimitive.Separator
			data-slot="dropdown-menu-separator"
			className={cn("-mx-1 my-1 h-px bg-border-subtle", className)}
			{...props}
		/>
	);
}

interface DropdownMenuSubTriggerProps
	extends React.ComponentProps<typeof DropdownMenuPrimitive.SubTrigger> {
	inset?: boolean;
}

function DropdownMenuSubTrigger({
	className,
	inset,
	children,
	...props
}: DropdownMenuSubTriggerProps) {
	return (
		<DropdownMenuPrimitive.SubTrigger
			data-slot="dropdown-menu-sub-trigger"
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
		</DropdownMenuPrimitive.SubTrigger>
	);
}

function DropdownMenuSubContent({
	className,
	...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.SubContent>) {
	return (
		<DropdownMenuPrimitive.SubContent
			data-slot="dropdown-menu-sub-content"
			className={cn(menuContentClasses, className)}
			{...props}
		/>
	);
}

// Trailing kbd chip. Uses mono face + muted color to sit as metadata.
function DropdownMenuShortcut({
	className,
	...props
}: React.HTMLAttributes<HTMLSpanElement>) {
	return (
		<span
			data-slot="dropdown-menu-shortcut"
			className={cn(
				"ml-auto font-mono text-xs tracking-wide text-text-muted",
				className,
			)}
			{...props}
		/>
	);
}

export {
	DropdownMenu,
	DropdownMenuTrigger,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuCheckboxItem,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuGroup,
	DropdownMenuSub,
	DropdownMenuSubTrigger,
	DropdownMenuSubContent,
	DropdownMenuShortcut,
	menuItemClasses,
	menuItemDangerClasses,
	menuContentClasses,
};
