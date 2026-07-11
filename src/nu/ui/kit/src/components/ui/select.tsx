import { cva, type VariantProps } from "class-variance-authority";
import { Check, ChevronDown, ChevronUp } from "lucide-react";
import { Select as SelectPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

// Radix Select wrapped with kit tokens. Trigger reads like the Input primitive
// (design/primitives.md §Select) so form rows stay flush. Content is a
// portal-mounted popover styled per design/palette.md §accent-wash for
// highlighted rows.

const selectTriggerVariants = cva(
	[
		"flex w-full items-center justify-between gap-2 rounded-md whitespace-nowrap",
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
				ghost: "bg-transparent text-text-primary border-transparent hover:bg-bg-elevated",
				filled: "bg-bg-elevated text-text-primary border-transparent hover:bg-bg-sunken",
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

function Select(props: React.ComponentProps<typeof SelectPrimitive.Root>) {
	return <SelectPrimitive.Root data-slot="select" {...props} />;
}

function SelectGroup(props: React.ComponentProps<typeof SelectPrimitive.Group>) {
	return <SelectPrimitive.Group data-slot="select-group" {...props} />;
}

function SelectValue(props: React.ComponentProps<typeof SelectPrimitive.Value>) {
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

function SelectContent({
	className,
	children,
	position = "popper",
	...props
}: React.ComponentProps<typeof SelectPrimitive.Content>) {
	return (
		<SelectPrimitive.Portal>
			<SelectPrimitive.Content
				data-slot="select-content"
				position={position}
				className={cn(
					"relative z-50 min-w-[8rem] overflow-hidden rounded-md",
					"bg-bg-elevated text-text-primary border border-border-default shadow-lg",
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
	return (
		<SelectPrimitive.Label
			data-slot="select-label"
			className={cn("px-2 py-1.5 text-xs font-medium text-text-secondary", className)}
			{...props}
		/>
	);
}

function SelectItem({
	className,
	children,
	...props
}: React.ComponentProps<typeof SelectPrimitive.Item>) {
	return (
		<SelectPrimitive.Item
			data-slot="select-item"
			className={cn(
				"relative flex w-full cursor-default select-none items-center gap-2 rounded-sm py-1.5 pl-2 pr-8 text-base outline-hidden",
				"text-text-primary",
				"focus:bg-accent-wash focus:text-text-primary",
				"data-[highlighted]:bg-accent-wash data-[highlighted]:text-text-primary",
				"data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
				"[&>svg]:pointer-events-none [&>svg]:size-4 [&>svg]:shrink-0",
				className,
			)}
			{...props}
		>
			<span className="absolute right-2 flex size-3.5 items-center justify-center">
				<SelectPrimitive.ItemIndicator>
					<Check className="size-4 text-accent" />
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
	return (
		<SelectPrimitive.Separator
			data-slot="select-separator"
			className={cn("-mx-1 my-1 h-px bg-border-subtle", className)}
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
