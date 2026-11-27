import { cva, type VariantProps } from "class-variance-authority";
import { Check, ChevronDown, ChevronUp } from "lucide-react";
import { Select as SelectPrimitive } from "radix-ui";
import * as React from "react";

import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import {
	BottomSheet,
	BottomSheetContent,
	BottomSheetItem,
	BottomSheetTrigger,
} from "./bottom-sheet";

// Radix Select wrapped with kit tokens. Trigger reads like the Input primitive
// (design/primitives.md §Select) so form rows stay flush. Content is a
// portal-mounted popover styled per design/palette.md (bg-hover highlight) for
// highlighted rows.
//
// In touch mode (../../lib/touch.ts) the same parts render the options as
// rows of a bottom sheet (./bottom-sheet.tsx), the way popover.tsx does it.
// Radix Select cannot live in a sheet (it positions and focus-manages its own
// list), so touch mode keeps its own small state: the value, the open sheet,
// and the label of each option. Radix finds the picked option's label by
// rendering the closed list off screen; here the content renders its items a
// second time in a "collect" pass that paints nothing and only tells the
// value which label goes with which option, so the trigger reads right while
// the sheet is shut.

const selectTriggerVariants = cva(
	[
		"flex w-full items-center justify-between gap-2 rounded-md whitespace-nowrap",
		"cursor-default",
		"border transition-[border-color,box-shadow] duration-fast ease-out",
		"placeholder:text-text-muted",
		"focus:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-bg-sunken",
		"data-[placeholder]:text-text-muted",
		"[&>span]:truncate [&>svg]:pointer-events-none [&>svg]:shrink-0",
	].join(" "),
	{
		variants: {
			variant: {
				default: "bg-bg-surface text-text-primary border-border-default hover:border-border-strong",
				ghost: "bg-transparent text-text-primary border-transparent hover:bg-bg-hover",
				filled: "bg-bg-hover text-text-primary border-transparent hover:bg-bg-press",
			},
			size: {
				sm: "h-6 px-2 text-sm [&>svg]:size-3.5",
				md: "h-8 px-2.5 text-lg [&>svg]:size-4",
				lg: "h-10 px-3 text-lg [&>svg]:size-4",
			},
			invalid: {
				true: "border-status-danger focus-visible:ring-status-danger",
				false: "",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
			invalid: false,
		},
	},
);

// ---- touch mode -------------------------------------------------------------

interface TouchSelectValue {
	value: string;
	pick: (value: string) => void;
	open: boolean;
	setOpen: (open: boolean) => void;
	disabled?: boolean;
	/** The label of each option, as the collect pass found them. */
	labels: Map<string, React.ReactNode>;
	/** Moves when `labels` does, so readers of the context render again. */
	version: number;
	register: (value: string, label: React.ReactNode) => () => void;
}

const TouchSelectContext = React.createContext<TouchSelectValue | null>(null);
// True inside the content's collect pass: items register, nothing paints.
const CollectContext = React.createContext(false);

function useTouchSelect(): TouchSelectValue {
	const ctx = React.useContext(TouchSelectContext);
	if (!ctx) throw new Error("Select parts must be used inside <Select>");
	return ctx;
}

function TouchSelect({
	value: valueProp,
	defaultValue = "",
	onValueChange,
	open: openProp,
	defaultOpen = false,
	onOpenChange,
	disabled,
	name,
	required,
	form,
	children,
}: React.ComponentProps<typeof SelectPrimitive.Root>) {
	const [valueState, setValueState] = React.useState(defaultValue);
	const [openState, setOpenState] = React.useState(defaultOpen);
	const value = valueProp ?? valueState;
	const open = openProp ?? openState;
	const labels = React.useRef(new Map<string, React.ReactNode>()).current;
	// Bumped when the options change, so the trigger reads the new labels.
	const [version, setVersion] = React.useState(0);

	const register = React.useCallback(
		(key: string, label: React.ReactNode) => {
			const before = labels.get(key);
			labels.set(key, label);
			// A label is a node, a new object each render: only a new option or
			// a changed text label is news, or every render would bump again.
			if (before === undefined || (typeof label !== "object" && before !== label)) {
				setVersion((v) => v + 1);
			}
			return () => {
				labels.delete(key);
				setVersion((v) => v + 1);
			};
		},
		[labels],
	);

	const ctx = React.useMemo<TouchSelectValue>(
		() => ({
			value,
			pick: (next) => {
				if (valueProp === undefined) setValueState(next);
				onValueChange?.(next);
			},
			open,
			setOpen: (next) => {
				if (openProp === undefined) setOpenState(next);
				onOpenChange?.(next);
			},
			disabled,
			labels,
			version,
			register,
		}),
		[
			value,
			valueProp,
			onValueChange,
			open,
			openProp,
			onOpenChange,
			disabled,
			labels,
			version,
			register,
		],
	);

	return (
		<TouchSelectContext.Provider value={ctx}>
			<BottomSheet open={open} onOpenChange={ctx.setOpen}>
				{children}
			</BottomSheet>
			{name ? (
				<input type="hidden" name={name} value={value} required={required} form={form} />
			) : null}
		</TouchSelectContext.Provider>
	);
}

// ---- parts --------------------------------------------------------------------

function Select(props: React.ComponentProps<typeof SelectPrimitive.Root>) {
	const touch = useTouch();
	if (touch) return <TouchSelect {...props} />;
	return <SelectPrimitive.Root data-slot="select" {...props} />;
}

function SelectGroup(props: React.ComponentProps<typeof SelectPrimitive.Group>) {
	const touch = useTouch();
	const collecting = React.useContext(CollectContext);
	if (collecting) return <>{props.children}</>;
	if (touch) {
		const { asChild: _asChild, ...rest } = props;
		// biome-ignore lint/a11y/useSemanticElements: an option group in a listbox, not a form fieldset.
		return <div role="group" data-slot="select-group" {...rest} />;
	}
	return <SelectPrimitive.Group data-slot="select-group" {...props} />;
}

function TouchSelectValue({
	placeholder,
	children,
	className,
}: React.ComponentProps<typeof SelectPrimitive.Value>) {
	const ctx = useTouchSelect();
	const label = ctx.value ? ctx.labels.get(ctx.value) : undefined;
	return (
		<span data-slot="select-value" className={className}>
			{children ?? label ?? (ctx.value ? ctx.value : placeholder)}
		</span>
	);
}

function SelectValue(props: React.ComponentProps<typeof SelectPrimitive.Value>) {
	const touch = useTouch();
	if (touch) return <TouchSelectValue {...props} />;
	return <SelectPrimitive.Value data-slot="select-value" {...props} />;
}

interface SelectTriggerProps
	extends React.ComponentProps<typeof SelectPrimitive.Trigger>,
		VariantProps<typeof selectTriggerVariants> {}

function SelectTrigger({
	className,
	variant,
	size,
	invalid,
	children,
	...props
}: SelectTriggerProps) {
	const touch = useTouch();
	if (touch) {
		return (
			<TouchSelectTrigger
				className={cn(selectTriggerVariants({ variant, size, invalid, className }))}
				invalid={invalid}
				{...props}
			>
				{children}
			</TouchSelectTrigger>
		);
	}
	return (
		<SelectPrimitive.Trigger
			data-slot="select-trigger"
			aria-invalid={invalid || undefined}
			className={cn(selectTriggerVariants({ variant, size, invalid, className }))}
			{...props}
		>
			{children}
			<SelectPrimitive.Icon asChild>
				<ChevronDown className="opacity-60" />
			</SelectPrimitive.Icon>
		</SelectPrimitive.Trigger>
	);
}

function TouchSelectTrigger({
	invalid,
	disabled,
	children,
	asChild: _asChild,
	...props
}: React.ComponentProps<typeof SelectPrimitive.Trigger> & { invalid?: boolean | null }) {
	const ctx = useTouchSelect();
	return (
		<BottomSheetTrigger
			data-slot="select-trigger"
			role="combobox"
			aria-expanded={ctx.open}
			aria-invalid={invalid || undefined}
			data-placeholder={ctx.value ? undefined : ""}
			disabled={ctx.disabled || disabled}
			{...props}
		>
			{children}
			<ChevronDown className="opacity-60" aria-hidden="true" />
		</BottomSheetTrigger>
	);
}

function SelectScrollUpButton({
	className,
	...props
}: React.ComponentProps<typeof SelectPrimitive.ScrollUpButton>) {
	return (
		<SelectPrimitive.ScrollUpButton
			data-slot="select-scroll-up"
			className={cn(
				"flex cursor-default items-center justify-center py-1 text-text-secondary",
				className,
			)}
			{...props}
		>
			<ChevronUp className="size-4" />
		</SelectPrimitive.ScrollUpButton>
	);
}

function SelectScrollDownButton({
	className,
	...props
}: React.ComponentProps<typeof SelectPrimitive.ScrollDownButton>) {
	return (
		<SelectPrimitive.ScrollDownButton
			data-slot="select-scroll-down"
			className={cn(
				"flex cursor-default items-center justify-center py-1 text-text-secondary",
				className,
			)}
			{...props}
		>
			<ChevronDown className="size-4" />
		</SelectPrimitive.ScrollDownButton>
	);
}

// The options twice: once in the collect pass, always mounted, painting
// nothing, so the trigger knows each option's label; once as the sheet's
// rows while it is open. The caller's classes style the sheet body, as in
// popover.tsx.
function TouchSelectContent({
	className,
	children,
	"aria-label": ariaLabel,
}: React.ComponentProps<typeof SelectPrimitive.Content>) {
	return (
		<>
			<CollectContext.Provider value={true}>{children}</CollectContext.Provider>
			<BottomSheetContent
				label={ariaLabel ?? "Options"}
				bodyClassName={cn(className, "w-full max-w-none")}
			>
				<div role="listbox" data-slot="select-content">
					{children}
				</div>
			</BottomSheetContent>
		</>
	);
}

function SelectContent({
	className,
	children,
	position = "popper",
	...props
}: React.ComponentProps<typeof SelectPrimitive.Content>) {
	const touch = useTouch();
	if (touch) {
		return (
			<TouchSelectContent className={className} aria-label={props["aria-label"]}>
				{children}
			</TouchSelectContent>
		);
	}
	return (
		<SelectPrimitive.Portal>
			<SelectPrimitive.Content
				data-slot="select-content"
				position={position}
				className={cn(
					"relative z-50 min-w-[8rem] overflow-hidden rounded-md",
					"bg-bg-elevated text-text-primary border border-border-default shadow-floating",
					"data-[state=open]:duration-base data-[state=open]:ease-out",
					"data-[state=closed]:duration-base data-[state=closed]:ease-in",
					"data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
					"data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
					"data-[side=bottom]:slide-in-from-top-1 data-[side=top]:slide-in-from-bottom-1",
					position === "popper" &&
						"data-[side=bottom]:translate-y-1 data-[side=top]:-translate-y-1",
					className,
				)}
				{...props}
			>
				<SelectScrollUpButton />
				<SelectPrimitive.Viewport
					className={cn(
						"p-1",
						position === "popper" &&
							"h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]",
					)}
				>
					{children}
				</SelectPrimitive.Viewport>
				<SelectScrollDownButton />
			</SelectPrimitive.Content>
		</SelectPrimitive.Portal>
	);
}

function SelectLabel({
	className,
	...props
}: React.ComponentProps<typeof SelectPrimitive.Label>) {
	const touch = useTouch();
	const collecting = React.useContext(CollectContext);
	if (collecting) return null;
	if (touch) {
		const { asChild: _asChild, ...rest } = props;
		return (
			<div
				data-slot="select-label"
				className={cn("px-1 pt-3 pb-1 text-xs font-medium text-text-secondary", className)}
				{...rest}
			/>
		);
	}
	return (
		<SelectPrimitive.Label
			data-slot="select-label"
			className={cn("px-2 py-1.5 text-xs font-medium text-text-secondary", className)}
			{...props}
		/>
	);
}

// A sheet row in touch mode; in the collect pass, only its label.
function TouchSelectItem({
	className,
	children,
	value,
	disabled,
}: React.ComponentProps<typeof SelectPrimitive.Item>) {
	const ctx = useTouchSelect();
	const collecting = React.useContext(CollectContext);
	const { register } = ctx;
	React.useLayoutEffect(() => {
		if (collecting) return register(value, children);
	}, [collecting, register, value, children]);
	if (collecting) return null;
	const selected = value === ctx.value;
	return (
		<BottomSheetItem
			role="option"
			aria-selected={selected}
			data-slot="select-item"
			selected={selected}
			disabled={disabled}
			className={className}
			onClick={() => {
				ctx.pick(value);
				ctx.setOpen(false);
			}}
		>
			<span className="min-w-0 flex-1 truncate">{children}</span>
			{selected ? <Check className="text-accent-text!" aria-hidden="true" /> : null}
		</BottomSheetItem>
	);
}

function SelectItem({
	className,
	children,
	...props
}: React.ComponentProps<typeof SelectPrimitive.Item>) {
	const touch = useTouch();
	if (touch) {
		return (
			<TouchSelectItem className={className} {...props}>
				{children}
			</TouchSelectItem>
		);
	}
	return (
		<SelectPrimitive.Item
			data-slot="select-item"
			className={cn(
				"relative flex w-full cursor-default select-none items-center gap-2 rounded-sm py-1.5 pl-2 pr-8 text-base outline-hidden",
				"text-text-primary",
				"focus:bg-bg-hover focus:text-text-primary",
				"data-[highlighted]:bg-bg-hover data-[highlighted]:text-text-primary",
				"data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
				"[&>svg]:pointer-events-none [&>svg]:size-4 [&>svg]:shrink-0",
				className,
			)}
			{...props}
		>
			<span className="absolute right-2 flex size-3.5 items-center justify-center">
				<SelectPrimitive.ItemIndicator>
					<Check className="size-4 text-accent-text" />
				</SelectPrimitive.ItemIndicator>
			</span>
			<SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
		</SelectPrimitive.Item>
	);
}

function SelectSeparator({
	className,
	...props
}: React.ComponentProps<typeof SelectPrimitive.Separator>) {
	const touch = useTouch();
	const collecting = React.useContext(CollectContext);
	if (collecting) return null;
	// Sheet rows carry their own rule: a gap is the break between groups.
	if (touch) {
		return <div aria-hidden="true" data-slot="select-separator" className={cn("h-3", className)} />;
	}
	return (
		<SelectPrimitive.Separator
			data-slot="select-separator"
			className={cn("-mx-1 my-1 h-px bg-border-default", className)}
			{...props}
		/>
	);
}

export {
	Select,
	SelectContent,
	SelectGroup,
	SelectItem,
	SelectLabel,
	SelectSeparator,
	SelectTrigger,
	SelectValue,
	selectTriggerVariants,
};
