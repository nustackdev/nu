import { Command as CommandPrimitive } from "cmdk";
import { Check, ChevronsUpDown, Search } from "lucide-react";
import { Popover as PopoverPrimitive } from "radix-ui";
import * as React from "react";

import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import { BottomSheet, BottomSheetContent, BottomSheetTrigger } from "./bottom-sheet";
import { selectTriggerVariants } from "./select";

// Combobox is Popover + cmdk. No Radix primitive covers the free-text +
// filterable menu shape (design/primitives.md §Combobox). Trigger reuses
// the Select trigger's visual variants so form rows read as one family.
//
// In touch mode (../../lib/touch.ts) the list opens in a bottom sheet
// (./bottom-sheet.tsx), the pattern in popover.tsx: the search field pinned
// to the top of the sheet, the options under it as 44px rows. The field is
// not focused when the sheet opens, so the on-screen keyboard stays down
// until the person taps it: most picks are a scroll and a tap, not a search.

interface ComboboxContextValue {
	open: boolean;
	setOpen: (open: boolean) => void;
	value: string;
	onValueChange: (value: string) => void;
}

const ComboboxContext = React.createContext<ComboboxContextValue | null>(null);

function useComboboxContext() {
	const ctx = React.useContext(ComboboxContext);
	if (!ctx) {
		throw new Error("Combobox parts must be used inside <Combobox>");
	}
	return ctx;
}

interface ComboboxProps {
	value?: string;
	defaultValue?: string;
	onValueChange?: (value: string) => void;
	open?: boolean;
	defaultOpen?: boolean;
	onOpenChange?: (open: boolean) => void;
	children?: React.ReactNode;
}

function Combobox({
	value: valueProp,
	defaultValue = "",
	onValueChange,
	open: openProp,
	defaultOpen = false,
	onOpenChange,
	children,
}: ComboboxProps) {
	const [openState, setOpenState] = React.useState(defaultOpen);
	const [valueState, setValueState] = React.useState(defaultValue);

	const open = openProp ?? openState;
	const value = valueProp ?? valueState;

	const setOpen = React.useCallback(
		(next: boolean) => {
			if (openProp === undefined) setOpenState(next);
			onOpenChange?.(next);
		},
		[openProp, onOpenChange],
	);

	const setValue = React.useCallback(
		(next: string) => {
			if (valueProp === undefined) setValueState(next);
			onValueChange?.(next);
		},
		[valueProp, onValueChange],
	);

	const ctx = React.useMemo<ComboboxContextValue>(
		() => ({ open, setOpen, value, onValueChange: setValue }),
		[open, setOpen, value, setValue],
	);

	const touch = useTouch();
	return (
		<ComboboxContext.Provider value={ctx}>
			{touch ? (
				<BottomSheet open={open} onOpenChange={setOpen}>
					{children}
				</BottomSheet>
			) : (
				<PopoverPrimitive.Root open={open} onOpenChange={setOpen}>
					{children}
				</PopoverPrimitive.Root>
			)}
		</ComboboxContext.Provider>
	);
}

interface ComboboxTriggerProps
	extends React.ComponentProps<typeof PopoverPrimitive.Trigger> {
	variant?: "default" | "ghost" | "filled";
	size?: "sm" | "md" | "lg";
	invalid?: boolean;
}

function ComboboxTrigger({
	className,
	variant,
	size,
	invalid,
	children,
	...props
}: ComboboxTriggerProps) {
	const ctx = useComboboxContext();
	const touch = useTouch();
	const Trigger = touch ? BottomSheetTrigger : PopoverPrimitive.Trigger;
	return (
		<Trigger
			data-slot="combobox-trigger"
			role="combobox"
			aria-expanded={ctx.open}
			aria-invalid={invalid || undefined}
			className={cn(selectTriggerVariants({ variant, size, invalid, className }))}
			{...props}
		>
			{children}
			<ChevronsUpDown className="opacity-60" />
		</Trigger>
	);
}

function ComboboxContent({
	className,
	children,
	align = "start",
	sideOffset = 4,
	...props
}: React.ComponentProps<typeof PopoverPrimitive.Content>) {
	const touch = useTouch();
	if (touch) {
		// Placement means nothing at the bottom of the screen. No overflow clip
		// on the list's box, so the search field can stick to the sheet's top.
		return (
			<BottomSheetContent
				label={props["aria-label"] ?? "Options"}
				bodyClassName={cn(className, "w-full max-w-none")}
				onOpenAutoFocus={(e) => {
					e.preventDefault();
					(e.currentTarget as HTMLElement | null)?.focus();
				}}
			>
				<CommandPrimitive data-slot="combobox-content" className="flex w-full flex-col">
					{children}
				</CommandPrimitive>
			</BottomSheetContent>
		);
	}
	return (
		<PopoverPrimitive.Portal>
			<PopoverPrimitive.Content
				data-slot="combobox-content"
				align={align}
				sideOffset={sideOffset}
				className={cn(
					"z-50 w-[var(--radix-popover-trigger-width)] min-w-[8rem] overflow-hidden rounded-md",
					"bg-bg-elevated text-text-primary border border-border-default shadow-floating",
					"data-[state=open]:duration-base data-[state=open]:ease-out",
					"data-[state=closed]:duration-base data-[state=closed]:ease-in",
					"data-[state=open]:animate-in data-[state=open]:fade-in-0",
					"data-[state=closed]:animate-out data-[state=closed]:fade-out-0",
					"data-[side=bottom]:slide-in-from-top-1 data-[side=top]:slide-in-from-bottom-1",
					className,
				)}
				{...props}
			>
				<CommandPrimitive className="flex w-full flex-col overflow-hidden">
					{children}
				</CommandPrimitive>
			</PopoverPrimitive.Content>
		</PopoverPrimitive.Portal>
	);
}

function ComboboxInput({
	className,
	...props
}: React.ComponentProps<typeof CommandPrimitive.Input>) {
	const touch = useTouch();
	return (
		<div
			className={cn(
				"flex items-center gap-2 border-b border-border-subtle px-2.5",
				// Pinned to the sheet's top while the options scroll under it.
				touch && "sticky top-0 z-10 bg-bg-elevated",
			)}
			data-slot="combobox-input-wrap"
		>
			<Search className="size-4 shrink-0 text-text-muted" aria-hidden="true" />
			<CommandPrimitive.Input
				data-slot="combobox-input"
				className={cn(
					"flex h-8 w-full bg-transparent text-base outline-hidden",
					"text-text-primary placeholder:text-text-muted",
					"disabled:cursor-not-allowed disabled:opacity-50",
					className,
				)}
				{...props}
			/>
		</div>
	);
}

function ComboboxList({
	className,
	...props
}: React.ComponentProps<typeof CommandPrimitive.List>) {
	const touch = useTouch();
	return (
		<CommandPrimitive.List
			data-slot="combobox-list"
			className={cn(
				"max-h-72 overflow-y-auto overflow-x-hidden p-1",
				// The sheet's body scrolls, not the list.
				touch && "max-h-none overflow-visible p-0",
				className,
			)}
			{...props}
		/>
	);
}

function ComboboxEmpty({
	className,
	...props
}: React.ComponentProps<typeof CommandPrimitive.Empty>) {
	return (
		<CommandPrimitive.Empty
			data-slot="combobox-empty"
			className={cn("py-6 text-center text-sm text-text-muted", className)}
			{...props}
		/>
	);
}

function ComboboxGroup({
	className,
	...props
}: React.ComponentProps<typeof CommandPrimitive.Group>) {
	return (
		<CommandPrimitive.Group
			data-slot="combobox-group"
			className={cn(
				"overflow-hidden text-text-primary",
				// cmdk emits `[cmdk-group-heading]` on the group's rendered label
				"[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-text-secondary",
				className,
			)}
			{...props}
		/>
	);
}

/** The look of a row in a combobox list, shared by the kit's other pickers over a list. */
const comboboxItemClass = [
	"relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-base outline-hidden",
	"text-text-primary",
	"data-[selected=true]:bg-bg-hover",
	"data-[highlighted=true]:bg-bg-hover",
	"aria-selected:bg-bg-hover",
	"data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
	"[&>svg]:pointer-events-none [&>svg]:size-4 [&>svg]:shrink-0",
].join(" ");

/**
 * Added to `comboboxItemClass` in touch mode: the row of a sheet, 44px, ruled
 * like `BottomSheetItem`. No resting highlight (cmdk marks the first match),
 * only the press: the pick is the check, not a tint.
 */
const comboboxTouchItemClass = [
	"min-h-11 rounded-none px-1 border-b border-border-subtle last:border-b-0",
	"data-[selected=true]:bg-transparent data-[highlighted=true]:bg-transparent aria-selected:bg-transparent",
	"active:bg-bg-press",
].join(" ");

interface ComboboxItemProps
	extends Omit<React.ComponentProps<typeof CommandPrimitive.Item>, "onSelect"> {
	onSelect?: (value: string) => void;
}

function ComboboxItem({
	className,
	children,
	value,
	onSelect,
	...props
}: ComboboxItemProps) {
	const ctx = useComboboxContext();
	const touch = useTouch();
	const selected = value !== undefined && value === ctx.value;
	return (
		<CommandPrimitive.Item
			data-slot="combobox-item"
			data-selected={selected || undefined}
			value={value}
			onSelect={(picked) => {
				ctx.onValueChange(picked);
				ctx.setOpen(false);
				onSelect?.(picked);
			}}
			className={cn(comboboxItemClass, touch && comboboxTouchItemClass, className)}
			{...props}
		>
			{children}
			{selected && <Check className="ml-auto size-4 text-accent-text" />}
		</CommandPrimitive.Item>
	);
}

export {
	Combobox,
	ComboboxContent,
	ComboboxEmpty,
	ComboboxGroup,
	ComboboxInput,
	ComboboxItem,
	ComboboxList,
	ComboboxTrigger,
	comboboxItemClass,
	comboboxTouchItemClass,
};
