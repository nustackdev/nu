import { Command as CommandPrimitive } from "cmdk";
import { Check, ChevronsUpDown, Search } from "lucide-react";
import { Popover as PopoverPrimitive } from "radix-ui";
import * as React from "react";

import { cn } from "../../lib/utils";
import { selectTriggerVariants } from "./select";

// Combobox is Popover + cmdk. No Radix primitive covers the free-text +
// filterable menu shape (design/primitives.md §Combobox). Trigger reuses
// the Select trigger's visual variants so form rows read as one family.

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

	return (
		<ComboboxContext.Provider value={ctx}>
			<PopoverPrimitive.Root open={open} onOpenChange={setOpen}>
				{children}
			</PopoverPrimitive.Root>
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
	return (
		<PopoverPrimitive.Trigger
			data-slot="combobox-trigger"
			role="combobox"
			aria-expanded={ctx.open}
			aria-invalid={invalid || undefined}
			className={cn(selectTriggerVariants({ variant, size, invalid, className }))}
			{...props}
		>
			{children}
			<ChevronsUpDown className="opacity-60" />
		</PopoverPrimitive.Trigger>
	);
}

function ComboboxContent({
	className,
	children,
	align = "start",
	sideOffset = 4,
	...props
}: React.ComponentProps<typeof PopoverPrimitive.Content>) {
	return (
		<PopoverPrimitive.Portal>
			<PopoverPrimitive.Content
				data-slot="combobox-content"
				align={align}
				sideOffset={sideOffset}
				className={cn(
					"z-50 w-[var(--radix-popover-trigger-width)] min-w-[8rem] overflow-hidden rounded-md",
					"bg-bg-elevated text-text-primary border border-border-default shadow-lg",
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
	return (
		<div className="flex items-center gap-2 border-b border-border-subtle px-2.5" data-slot="combobox-input-wrap">
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
	return (
		<CommandPrimitive.List
			data-slot="combobox-list"
			className={cn("max-h-72 overflow-y-auto overflow-x-hidden p-1", className)}
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
			className={cn(
				"relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-base outline-hidden",
				"text-text-primary",
				"data-[selected=true]:bg-accent-wash",
				"data-[highlighted=true]:bg-bg-elevated",
				"aria-selected:bg-bg-elevated",
				"data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
				"[&>svg]:pointer-events-none [&>svg]:size-4 [&>svg]:shrink-0",
				className,
			)}
			{...props}
		>
			{children}
			{selected && <Check className="ml-auto size-4 text-accent" />}
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
};
