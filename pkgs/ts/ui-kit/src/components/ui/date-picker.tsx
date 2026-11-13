import { format as formatDate } from "date-fns";
import { Calendar, ChevronLeft, ChevronRight, X } from "lucide-react";
import { Popover as PopoverPrimitive } from "radix-ui";
import * as React from "react";
import { DayPicker, type DateRange } from "react-day-picker";

import { cn } from "../../lib/utils";
import { IconButton } from "./icon-button";
import { selectTriggerVariants } from "./select";

// DatePicker = kit Popover + react-day-picker. react-day-picker owns keyboard
// nav and grid semantics; the wrapper paints their class hooks with kit
// tokens (design/primitives.md §DatePicker). Trigger reuses the Select
// trigger variants so form rows read as one family.

type Variant = "default" | "ghost" | "filled";
type Size = "sm" | "md" | "lg";

interface DatePickerBaseProps {
	variant?: Variant;
	size?: Size;
	invalid?: boolean;
	disabled?: boolean;
	placeholder?: string;
	format?: string;
	className?: string;
	id?: string;
	name?: string;
	"aria-label"?: string;
	/** More props for the trigger button (aria, a key handler, autofocus). */
	triggerProps?: React.ComponentProps<"button">;
	/** A clear button over the trigger while there is a value; Backspace or Delete on the trigger clears too. */
	clearable?: boolean;
	/** The clear button's accessible name. */
	clearLabel?: string;
	/** The calendar opened or closed. */
	onOpenChange?: (open: boolean) => void;
}

interface DatePickerProps extends DatePickerBaseProps {
	value?: Date | null;
	onValueChange?: (value: Date | null) => void;
	defaultValue?: Date | null;
	min?: Date;
	max?: Date;
}

interface DateRangePickerProps extends DatePickerBaseProps {
	value?: DateRange | null;
	onValueChange?: (value: DateRange | null) => void;
	defaultValue?: DateRange | null;
	min?: Date;
	max?: Date;
}

// react-day-picker v10 exposes `classNames` keyed by the UI enum values
// (design/primitives.md refers to react-day-picker classes). Painting these
// once keeps DatePicker + DateRangePicker visually in sync.
const dayPickerClassNames = {
	root: "p-3",
	months: "flex flex-col sm:flex-row gap-4",
	month: "space-y-2",
	month_caption: "flex justify-center pt-1 relative items-center h-8",
	caption_label: "text-base font-medium text-text-primary",
	nav: "flex items-center gap-1 absolute inset-x-0 top-1 justify-between px-1",
	button_previous:
		"inline-flex items-center justify-center size-7 rounded-sm text-text-secondary cursor-default hover:bg-bg-hover active:bg-bg-press hover:text-text-primary focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
	button_next:
		"inline-flex items-center justify-center size-7 rounded-sm text-text-secondary cursor-default hover:bg-bg-hover active:bg-bg-press hover:text-text-primary focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
	month_grid: "w-full border-collapse",
	weekdays: "flex",
	weekday: "text-text-muted w-8 font-normal text-xs uppercase tracking-wider",
	week: "flex w-full mt-1",
	day: "size-8 text-center text-sm p-0 relative focus-within:relative focus-within:z-20",
	day_button:
		"inline-flex items-center justify-center size-8 rounded-sm text-text-primary cursor-default hover:bg-bg-hover active:bg-bg-press focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset aria-selected:opacity-100",
	selected:
		"[&>button]:bg-accent [&>button]:text-accent-fg [&>button]:hover:bg-accent-hover",
	today: "[&>button]:border [&>button]:border-accent-line",
	outside: "[&>button]:text-text-muted",
	disabled: "[&>button]:opacity-50 [&>button]:pointer-events-none",
	range_start: "[&>button]:bg-accent [&>button]:text-accent-fg [&>button]:rounded-r-none",
	range_end: "[&>button]:bg-accent [&>button]:text-accent-fg [&>button]:rounded-l-none",
	range_middle:
		"bg-bg-press [&>button]:bg-transparent [&>button]:text-text-primary [&>button]:rounded-none [&>button]:hover:bg-bg-hover",
	hidden: "invisible",
} as const;

const dayPickerComponents = {
	// Swap react-day-picker's chevron for a lucide one so the icon set stays
	// consistent across the kit.
	Chevron: (props: { className?: string; orientation?: "left" | "right" | "up" | "down" }) => {
		const cls = cn("size-4", props.className);
		if (props.orientation === "right") return <ChevronRight className={cls} />;
		return <ChevronLeft className={cls} />;
	},
};

function TriggerSurface({
	variant,
	size,
	invalid,
	disabled,
	className,
	label,
	empty,
	id,
	ariaLabel,
	name,
	open,
	triggerProps,
	clearing,
}: {
	variant?: Variant;
	size?: Size;
	invalid?: boolean;
	disabled?: boolean;
	className?: string;
	label: string;
	empty: boolean;
	id?: string;
	ariaLabel?: string;
	name?: string;
	open: boolean;
	triggerProps?: React.ComponentProps<"button">;
	/** A clear button sits over the trigger's end: leave room, drop the calendar glyph. */
	clearing?: boolean;
}) {
	return (
		<PopoverPrimitive.Trigger
			{...triggerProps}
			data-slot="date-picker-trigger"
			data-empty={empty || undefined}
			disabled={disabled}
			aria-invalid={invalid || undefined}
			aria-label={ariaLabel}
			aria-expanded={open}
			id={id}
			name={name}
			className={cn(
				selectTriggerVariants({ variant, size, invalid }),
				empty && "text-text-muted",
				clearing && "pr-8",
				className,
			)}
		>
			<span className="truncate">{label}</span>
			{clearing ? null : <Calendar className="opacity-60" />}
		</PopoverPrimitive.Trigger>
	);
}

// The clear button is a sibling of the trigger (a button may not hold a
// button), laid over the trigger's end. Clearing moves focus back to the
// trigger, since the clear button itself goes away with the value.
function Clearable({
	show,
	label,
	size,
	onClear,
	children,
}: {
	show: boolean;
	label: string;
	size?: Size;
	onClear: () => void;
	children: React.ReactNode;
}) {
	const box = React.useRef<HTMLDivElement>(null);
	return (
		<div ref={box} data-slot="date-picker-clearable" className="relative w-full">
			{children}
			{show ? (
				<IconButton
					variant="ghost"
					size={size === "lg" ? "sm" : "xs"}
					aria-label={label}
					className="absolute right-1.5 top-1/2 -translate-y-1/2"
					onClick={() => {
						onClear();
						box.current
							?.querySelector<HTMLButtonElement>('[data-slot="date-picker-trigger"]')
							?.focus();
					}}
				>
					<X aria-hidden />
				</IconButton>
			) : null}
		</div>
	);
}

/** The trigger's key handler with Backspace and Delete clearing, after the caller's own. */
function clearKeys(
	triggerProps: React.ComponentProps<"button"> | undefined,
	clear: (() => void) | null,
): React.ComponentProps<"button"> | undefined {
	if (!clear) return triggerProps;
	return {
		...triggerProps,
		onKeyDown: (e) => {
			triggerProps?.onKeyDown?.(e);
			if (e.defaultPrevented) return;
			if (e.key !== "Backspace" && e.key !== "Delete") return;
			e.preventDefault();
			clear();
		},
	};
}

function popoverContentClasses(className?: string) {
	return cn(
		"z-50 rounded-md bg-bg-elevated text-text-primary border border-border-default shadow-floating",
		"data-[state=open]:duration-base data-[state=open]:ease-out",
		"data-[state=closed]:duration-base data-[state=closed]:ease-in",
		"data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
		"data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
		"data-[side=bottom]:slide-in-from-top-1 data-[side=top]:slide-in-from-bottom-1",
		className,
	);
}

function DatePicker({
	value: valueProp,
	defaultValue = null,
	onValueChange,
	variant,
	size,
	invalid,
	disabled,
	placeholder = "Pick a date",
	format = "PP",
	className,
	min,
	max,
	id,
	name,
	"aria-label": ariaLabel,
	triggerProps,
	clearable = false,
	clearLabel = "Clear date",
	onOpenChange,
}: DatePickerProps) {
	const [internal, setInternal] = React.useState<Date | null>(defaultValue);
	const value = valueProp === undefined ? internal : valueProp;
	const [open, setOpenState] = React.useState(false);
	const setOpen = (next: boolean) => {
		setOpenState(next);
		onOpenChange?.(next);
	};

	const setValue = (next: Date | null) => {
		if (valueProp === undefined) setInternal(next);
		onValueChange?.(next);
	};

	const label = value ? formatDate(value, format) : placeholder;
	const clearing = clearable && Boolean(value) && !disabled;
	const clear = clearing ? () => setValue(null) : null;

	const picker = (
		<PopoverPrimitive.Root open={open} onOpenChange={setOpen}>
			<TriggerSurface
				variant={variant}
				size={size}
				invalid={invalid}
				disabled={disabled}
				className={className}
				label={label}
				empty={!value}
				id={id}
				ariaLabel={ariaLabel}
				name={name}
				open={open}
				triggerProps={clearKeys(triggerProps, clear)}
				clearing={clearing}
			/>
			<PopoverPrimitive.Portal>
				<PopoverPrimitive.Content
					data-slot="date-picker-content"
					align="start"
					sideOffset={4}
					className={popoverContentClasses()}
				>
					<DayPicker
						mode="single"
						selected={value ?? undefined}
						defaultMonth={value ?? undefined}
						onSelect={(next) => {
							setValue(next ?? null);
							if (next) setOpen(false);
						}}
						disabled={
							min || max
								? [
										...(min ? [{ before: min }] : []),
										...(max ? [{ after: max }] : []),
									]
								: undefined
						}
						classNames={dayPickerClassNames}
						components={dayPickerComponents}
					/>
				</PopoverPrimitive.Content>
			</PopoverPrimitive.Portal>
		</PopoverPrimitive.Root>
	);
	if (!clearable) return picker;
	return (
		<Clearable show={clearing} label={clearLabel} size={size} onClear={() => setValue(null)}>
			{picker}
		</Clearable>
	);
}

function DateRangePicker({
	value: valueProp,
	defaultValue = null,
	onValueChange,
	variant,
	size,
	invalid,
	disabled,
	placeholder = "Pick a range",
	format = "PP",
	className,
	min,
	max,
	id,
	name,
	"aria-label": ariaLabel,
	triggerProps,
	clearable = false,
	clearLabel = "Clear range",
	onOpenChange,
}: DateRangePickerProps) {
	const [internal, setInternal] = React.useState<DateRange | null>(defaultValue);
	const value = valueProp === undefined ? internal : valueProp;
	const [open, setOpenState] = React.useState(false);
	const setOpen = (next: boolean) => {
		setOpenState(next);
		onOpenChange?.(next);
	};

	const setValue = (next: DateRange | null) => {
		if (valueProp === undefined) setInternal(next);
		onValueChange?.(next);
	};

	const renderLabel = () => {
		if (!value || !value.from) return placeholder;
		if (!value.to) return formatDate(value.from, format);
		return `${formatDate(value.from, format)} - ${formatDate(value.to, format)}`;
	};

	const empty = !value || !value.from;
	const clearing = clearable && !empty && !disabled;
	const clear = clearing ? () => setValue(null) : null;

	const picker = (
		<PopoverPrimitive.Root open={open} onOpenChange={setOpen}>
			<TriggerSurface
				variant={variant}
				size={size}
				invalid={invalid}
				disabled={disabled}
				className={className}
				label={renderLabel()}
				empty={empty}
				id={id}
				ariaLabel={ariaLabel}
				name={name}
				open={open}
				triggerProps={clearKeys(triggerProps, clear)}
				clearing={clearing}
			/>
			<PopoverPrimitive.Portal>
				<PopoverPrimitive.Content
					data-slot="date-range-picker-content"
					align="start"
					sideOffset={4}
					className={popoverContentClasses()}
				>
					<DayPicker
						mode="range"
						numberOfMonths={2}
						selected={value ?? undefined}
						defaultMonth={value?.from}
						onSelect={(next) => setValue(next ?? null)}
						disabled={
							min || max
								? [
										...(min ? [{ before: min }] : []),
										...(max ? [{ after: max }] : []),
									]
								: undefined
						}
						classNames={dayPickerClassNames}
						components={dayPickerComponents}
					/>
				</PopoverPrimitive.Content>
			</PopoverPrimitive.Portal>
		</PopoverPrimitive.Root>
	);
	if (!clearable) return picker;
	return (
		<Clearable show={clearing} label={clearLabel} size={size} onClear={() => setValue(null)}>
			{picker}
		</Clearable>
	);
}

export { DatePicker, DateRangePicker };
export type { DatePickerProps, DateRangePickerProps };
