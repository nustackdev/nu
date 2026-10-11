// Accordion primitive. Wraps @radix-ui/react-accordion.
// Design refs:
//   primitives.md    §Accordion (compound parts, chevron auto-rotate)
//   palette.md       backgrounds, text tiers, borders
//   space-radius.md  §Density Accordion (header pad-y 12, content pad-top 8)
//   motion.md        §3 Accordion (content height base + ease-in-out, chevron
//                     rotate fast + ease-out)
//   a11y.md          §3 Accordion (Radix wires arrows, Space/Enter, Home/End)
//
// Content height animation uses Radix's --radix-accordion-content-height CSS
// var; consumers do not need to measure content themselves.
//
// Two variants. `plain` rows sit in the flow, separated by hairlines, the
// trigger a rounded hover pill. `boxed` draws the bordered container itself
// and runs every row flush to its edges: the trigger wash fills the row, the
// focus ring sits inside it, and trigger text and content share one inset.
// Never pad the items of a boxed accordion; the trigger and content own it.

import { Accordion as AccordionPrimitive } from "radix-ui";
import { ChevronDown } from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";

export function Accordion({
	className,
	variant = "plain",
	...props
}: React.ComponentProps<typeof AccordionPrimitive.Root> & { variant?: "plain" | "boxed" }) {
	return (
		<AccordionPrimitive.Root
			data-slot="accordion"
			data-variant={variant}
			className={cn(
				"group/accordion flex flex-col",
				variant === "boxed" && "overflow-hidden rounded-md border border-border-default",
				className,
			)}
			{...props}
		/>
	);
}

export function AccordionItem({
	className,
	...props
}: React.ComponentProps<typeof AccordionPrimitive.Item>) {
	return (
		<AccordionPrimitive.Item
			data-slot="accordion-item"
			className={cn(
				"border-b border-border-subtle last:border-b-0",
				className,
			)}
			{...props}
		/>
	);
}

export function AccordionTrigger({
	className,
	children,
	...props
}: React.ComponentProps<typeof AccordionPrimitive.Trigger>) {
	return (
		<AccordionPrimitive.Header className="flex">
			<AccordionPrimitive.Trigger
				data-slot="accordion-trigger"
				className={cn(
					"group flex flex-1 items-center justify-between gap-2",
					"rounded-md px-3 py-3 text-left text-base font-medium text-text-primary",
					"cursor-default",
					"transition-colors duration-fast ease-out",
					"hover:bg-bg-hover active:bg-bg-press",
					"disabled:pointer-events-none disabled:opacity-50",
					"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
					"group-data-[variant=boxed]/accordion:rounded-none group-data-[variant=boxed]/accordion:focus-visible:ring-inset group-data-[variant=boxed]/accordion:focus-visible:ring-offset-0",
					"[&_svg]:pointer-events-none [&_svg]:shrink-0",
					className,
				)}
				{...props}
			>
				{children}
				<ChevronDown
					aria-hidden
					className={cn(
						"size-4 text-text-secondary shrink-0",
						"transition-transform duration-fast ease-out",
						"group-data-[state=open]:rotate-180",
					)}
				/>
			</AccordionPrimitive.Trigger>
		</AccordionPrimitive.Header>
	);
}

export function AccordionContent({
	className,
	children,
	...props
}: React.ComponentProps<typeof AccordionPrimitive.Content>) {
	return (
		<AccordionPrimitive.Content
			data-slot="accordion-content"
			className={cn(
				// Radix wires --radix-accordion-content-height; the two named
				// keyframes below live in tw-animate-css.
				"overflow-hidden text-sm text-text-secondary",
				"data-[state=open]:animate-accordion-down",
				"data-[state=closed]:animate-accordion-up",
			)}
			{...props}
		>
			<div className={cn("px-3 pt-1 pb-3", className)}>{children}</div>
		</AccordionPrimitive.Content>
	);
}
