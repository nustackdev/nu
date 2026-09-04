// Tabs primitive. Wraps @radix-ui/react-tabs.
// Design refs:
//   primitives.md    §Tabs (variants pill / underline / segmented, compound parts)
//   palette.md       §2.4 accent for indicators, §2.3 borders
//   space-radius.md  §Density Tabs (32 row default, pad-y 6 pad-x 12)
//   motion.md        §3 Tabs indicator (base + ease-in-out for the moving line)
//   a11y.md          §3 Tabs (Radix wires roving tabindex, arrows, Home/End)
//
// TabsList variants:
//   line       underline under active trigger. Fleet-flavored default.
//   pill       accent-wash chip behind active. Reads as segmented navigation.
//   segmented  unified sunken bg with a raised surface pill on active.

import { cva, type VariantProps } from "class-variance-authority";
import { Tabs as TabsPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

// TabsList variants own the container chrome. Trigger active-state visuals
// are keyed off `data-variant` on the list so triggers stay a single component.
const tabsListVariants = cva(
	"inline-flex items-center text-text-secondary",
	{
		variants: {
			variant: {
				line: "border-b border-border-subtle gap-1",
				pill: "gap-1",
				segmented:
					"bg-bg-sunken border border-border-default rounded-md p-1 gap-1",
			},
		},
		defaultVariants: {
			variant: "line",
		},
	},
);

const tabsTriggerVariants = cva(
	[
		"inline-flex items-center justify-center gap-2 whitespace-nowrap",
		"font-medium text-text-secondary",
		"cursor-pointer",
		"transition-colors duration-fast ease-out",
		"disabled:pointer-events-none disabled:opacity-50",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"data-[state=active]:text-text-primary",
		"hover:text-text-primary",
		"[&_svg]:pointer-events-none [&_svg]:shrink-0",
	].join(" "),
	{
		variants: {
			size: {
				sm: "h-6 px-2 text-sm [&_svg]:size-3.5",
				md: "h-8 px-3 text-base [&_svg]:size-4",
				lg: "h-10 px-4 text-lg [&_svg]:size-4",
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

// Bridge list variant -> trigger active look. Kept out of the trigger cva
// because the flavor is a property of the list, not the trigger.
const triggerVariantClass = {
	line: [
		"relative rounded-none",
		// 2px accent underline sits just under the row baseline.
		"data-[state=active]:after:absolute data-[state=active]:after:left-0",
		"data-[state=active]:after:right-0 data-[state=active]:after:-bottom-px",
		"data-[state=active]:after:h-0.5 data-[state=active]:after:bg-accent",
		"data-[state=active]:after:content-['']",
		"data-[state=active]:after:transition-transform data-[state=active]:after:duration-base data-[state=active]:after:ease-in-out",
	].join(" "),
	pill: [
		"rounded-md",
		"data-[state=active]:bg-accent-wash data-[state=active]:text-text-primary",
	].join(" "),
	segmented: [
		"rounded-sm",
		"data-[state=active]:bg-bg-surface data-[state=active]:text-text-primary",
		"data-[state=active]:shadow-sm",
	].join(" "),
} as const;

export function Tabs({
	className,
	...props
}: React.ComponentProps<typeof TabsPrimitive.Root>) {
	return (
		<TabsPrimitive.Root
			data-slot="tabs"
			className={cn("flex flex-col gap-3", className)}
			{...props}
		/>
	);
}

export interface TabsListProps
	extends React.ComponentProps<typeof TabsPrimitive.List>,
		VariantProps<typeof tabsListVariants> {}

export function TabsList({
	className,
	variant,
	...props
}: TabsListProps) {
	return (
		<TabsPrimitive.List
			data-slot="tabs-list"
			data-variant={variant ?? "line"}
			className={cn(tabsListVariants({ variant }), className)}
			{...props}
		/>
	);
}

export interface TabsTriggerProps
	extends React.ComponentProps<typeof TabsPrimitive.Trigger>,
		VariantProps<typeof tabsTriggerVariants> {
	variant?: "line" | "pill" | "segmented";
}

// Trigger takes an explicit `variant` too so consumers can render one trigger
// with a different active treatment, but the common case leaves it undefined
// and reads the parent list flavor via the class map below.
export function TabsTrigger({
	className,
	size,
	variant = "line",
	...props
}: TabsTriggerProps) {
	return (
		<TabsPrimitive.Trigger
			data-slot="tabs-trigger"
			className={cn(
				tabsTriggerVariants({ size }),
				triggerVariantClass[variant],
				className,
			)}
			{...props}
		/>
	);
}

export function TabsContent({
	className,
	...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) {
	return (
		<TabsPrimitive.Content
			data-slot="tabs-content"
			className={cn(
				"outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
				className,
			)}
			{...props}
		/>
	);
}

export { tabsListVariants };
