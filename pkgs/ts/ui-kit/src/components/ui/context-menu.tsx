// ContextMenu primitive: right-click/long-press menu on a region.
// Design refs:
//   primitives.md    §ContextMenu (mirrors DropdownMenu shape)
//   motion.md        §3 ContextMenu (`duration-base` fade+scale, no y-shift)
//   a11y.md          §3 ContextMenu (Menu key / Shift+F10, then DropdownMenu keys)
//
// Item visual contract matches DropdownMenu exactly, so we reuse the item,
// separator and shortcut recipes from there. Content uses fade+scale
// motion (anchor is the cursor, y-shift would drift away from it).
//
// In touch mode (../../lib/touch.ts) a long-press opens it, as a bottom sheet
// (./menu-sheet.tsx, the same parts DropdownMenu uses). Long-press is about
// half a second with the finger held still; moving it (a scroll) cancels. The
// press also holds back the phone's own callout and text selection on the
// region, since long-press there means this menu. Android's own long-press
// `contextmenu` event opens it too.

import { ContextMenu as ContextMenuPrimitive, Slot as SlotPrimitive } from "radix-ui";
import { Check, ChevronRight, Circle } from "lucide-react";
import * as React from "react";

import { LONG_PRESS_MS, LONG_PRESS_SLOP, useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import {
	menuItemClasses,
	menuItemDangerClasses,
	menuSeparatorClasses,
	menuShortcutClasses,
} from "./dropdown-menu";
import {
	MenuSheet,
	MenuSheetCheckboxItem,
	type MenuSheetCheckboxItemProps,
	MenuSheetContent,
	MenuSheetGroup,
	MenuSheetItem,
	type MenuSheetItemProps,
	MenuSheetLabel,
	MenuSheetRadioGroup,
	MenuSheetRadioItem,
	type MenuSheetRadioItemProps,
	MenuSheetSeparator,
	MenuSheetSub,
	MenuSheetSubContent,
	MenuSheetSubTrigger,
	sheetContentProps,
	useMenuSheet,
} from "./menu-sheet";
import { Shortcut } from "./shortcut";

const contextMenuContentClasses = [
	"z-50 min-w-[10rem] overflow-hidden p-1",
	"bg-bg-elevated text-text-primary border border-border-default rounded-md shadow-floating",
	"data-[state=open]:animate-in data-[state=closed]:animate-out",
	"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
	"data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95",
	"data-[state=open]:duration-base data-[state=closed]:duration-base",
	"data-[state=open]:ease-out data-[state=closed]:ease-in",
].join(" ");

function ContextMenu({
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Root>) {
	const touch = useTouch();
	if (touch) {
		const { onOpenChange, children } = props;
		return <MenuSheet onOpenChange={onOpenChange}>{children}</MenuSheet>;
	}
	return <ContextMenuPrimitive.Root data-slot="context-menu" {...props} />;
}

function ContextMenuTrigger({
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Trigger>) {
	const touch = useTouch();
	if (touch) return <LongPressTrigger {...props} />;
	return (
		<ContextMenuPrimitive.Trigger data-slot="context-menu-trigger" {...props} />
	);
}

// The region in touch mode: a held finger opens the sheet. The tap that ends
// a long-press is swallowed, so a link or button under the finger does not
// also fire when the finger lifts.
function LongPressTrigger({
	asChild,
	disabled,
	style,
	onPointerDown,
	onPointerMove,
	onPointerUp,
	onPointerCancel,
	onPointerLeave,
	onClickCapture,
	onContextMenu,
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Trigger>) {
	const { setOpen } = useMenuSheet();
	const timer = React.useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
	const start = React.useRef<{ x: number; y: number } | null>(null);
	const fired = React.useRef(false);

	const cancel = React.useCallback(() => {
		clearTimeout(timer.current);
		timer.current = undefined;
		start.current = null;
	}, []);
	React.useEffect(() => cancel, [cancel]);

	const open = () => {
		cancel();
		fired.current = true;
		setOpen(true);
	};

	const Comp = asChild ? SlotPrimitive.Slot : "span";
	return (
		<Comp
			data-slot="context-menu-trigger"
			data-disabled={disabled || undefined}
			style={
				disabled
					? style
					: { WebkitTouchCallout: "none", WebkitUserSelect: "none", userSelect: "none", ...style }
			}
			onPointerDown={(e: React.PointerEvent<HTMLSpanElement>) => {
				onPointerDown?.(e);
				fired.current = false;
				if (disabled || e.defaultPrevented || e.button !== 0) return;
				cancel();
				start.current = { x: e.clientX, y: e.clientY };
				timer.current = setTimeout(open, LONG_PRESS_MS);
			}}
			onPointerMove={(e: React.PointerEvent<HTMLSpanElement>) => {
				onPointerMove?.(e);
				const from = start.current;
				if (from && Math.hypot(e.clientX - from.x, e.clientY - from.y) > LONG_PRESS_SLOP) cancel();
			}}
			onPointerUp={(e: React.PointerEvent<HTMLSpanElement>) => {
				onPointerUp?.(e);
				cancel();
			}}
			onPointerCancel={(e: React.PointerEvent<HTMLSpanElement>) => {
				onPointerCancel?.(e);
				cancel();
			}}
			onPointerLeave={(e: React.PointerEvent<HTMLSpanElement>) => {
				onPointerLeave?.(e);
				cancel();
			}}
			onClickCapture={(e: React.MouseEvent<HTMLSpanElement>) => {
				onClickCapture?.(e);
				if (!fired.current) return;
				fired.current = false;
				e.preventDefault();
				e.stopPropagation();
			}}
			onContextMenu={(e: React.MouseEvent<HTMLSpanElement>) => {
				onContextMenu?.(e);
				if (disabled || e.defaultPrevented) return;
				e.preventDefault();
				open();
			}}
			{...props}
		/>
	);
}

function ContextMenuGroup({
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Group>) {
	const touch = useTouch();
	if (touch) return <MenuSheetGroup {...props} />;
	return (
		<ContextMenuPrimitive.Group data-slot="context-menu-group" {...props} />
	);
}

function ContextMenuRadioGroup({
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.RadioGroup>) {
	const touch = useTouch();
	if (touch) return <MenuSheetRadioGroup {...props} />;
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
	const touch = useTouch();
	if (touch) return <MenuSheetSub {...props} />;
	return <ContextMenuPrimitive.Sub data-slot="context-menu-sub" {...props} />;
}

function ContextMenuContent({
	className,
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.Content>) {
	const touch = useTouch();
	if (touch) return <MenuSheetContent className={className} {...sheetContentProps(props)} />;
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
	const touch = useTouch();
	if (touch) {
		return (
			<MenuSheetItem
				variant={variant}
				inset={inset}
				className={className}
				{...(props as MenuSheetItemProps)}
			/>
		);
	}
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

// The check and the radio dot carry `!`: the item's own `[&_svg]` size and
// tint would otherwise win, drawing the dot as a full-size disc.
function ContextMenuCheckboxItem({
	className,
	children,
	checked,
	...props
}: React.ComponentProps<typeof ContextMenuPrimitive.CheckboxItem>) {
	const touch = useTouch();
	if (touch) {
		return (
			<MenuSheetCheckboxItem
				checked={checked}
				className={className}
				{...(props as MenuSheetCheckboxItemProps)}
			>
				{children}
			</MenuSheetCheckboxItem>
		);
	}
	return (
		<ContextMenuPrimitive.CheckboxItem
			data-slot="context-menu-checkbox-item"
			checked={checked}
			className={cn(menuItemClasses, "pl-8", className)}
			{...props}
		>
			<span className="absolute left-2 flex size-4 items-center justify-center">
				<ContextMenuPrimitive.ItemIndicator>
					<Check className="size-3.5! text-accent-text!" />
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
	const touch = useTouch();
	if (touch) {
		return (
			<MenuSheetRadioItem className={className} {...(props as MenuSheetRadioItemProps)}>
				{children}
			</MenuSheetRadioItem>
		);
	}
	return (
		<ContextMenuPrimitive.RadioItem
			data-slot="context-menu-radio-item"
			className={cn(menuItemClasses, "pl-8", className)}
			{...props}
		>
			<span className="absolute left-2 flex size-4 items-center justify-center">
				<ContextMenuPrimitive.ItemIndicator>
					<Circle className="size-2! fill-accent-text text-accent-text!" />
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
	const touch = useTouch();
	if (touch) return <MenuSheetLabel inset={inset} className={className} {...props} />;
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
	const touch = useTouch();
	if (touch) return <MenuSheetSeparator className={className} {...props} />;
	return (
		<ContextMenuPrimitive.Separator
			data-slot="context-menu-separator"
			className={cn(menuSeparatorClasses, className)}
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
	const touch = useTouch();
	if (touch) {
		return (
			<MenuSheetSubTrigger inset={inset} className={className} {...(props as MenuSheetItemProps)}>
				{children}
			</MenuSheetSubTrigger>
		);
	}
	return (
		<ContextMenuPrimitive.SubTrigger
			data-slot="context-menu-sub-trigger"
			className={cn(
				menuItemClasses,
				"data-[state=open]:bg-bg-hover",
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
	const touch = useTouch();
	if (touch) return <MenuSheetSubContent className={className} {...sheetContentProps(props)} />;
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
	keys,
	children,
	...props
}: React.HTMLAttributes<HTMLSpanElement> & {
	/** Key names, drawn as muted text (see `Shortcut`). Text children otherwise. */
	keys?: readonly string[];
}) {
	return (
		<span data-slot="context-menu-shortcut" className={cn(menuShortcutClasses, className)} {...props}>
			{keys ? <Shortcut keys={keys} variant="ghost" /> : children}
		</span>
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
