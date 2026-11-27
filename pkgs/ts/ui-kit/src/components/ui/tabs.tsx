// Tabs primitive. Wraps @radix-ui/react-tabs.
// Design refs:
//   primitives.md    §Tabs (variants pill / underline / segmented, compound parts)
//   palette.md       accent for indicators, borders
//   space-radius.md  §Density Tabs (32 row default, pad-y 6 pad-x 12)
//   motion.md        §3 Tabs indicator (base + ease-in-out for the moving line)
//   a11y.md          §3 Tabs (Radix wires roving tabindex, arrows, Home/End)
//
// TabsList variants:
//   line       underline under active trigger. Fleet-flavored default.
//   pill       press wash chip behind active. Reads as segmented navigation.
//   segmented  one press-wash track (like every kit track) with a raised surface pill on active.
//
// Narrow: a list never grows past its box. When its tabs run past the edge
// (a phone, a strip column, a dozen tabs on a wide desk) it scrolls sideways,
// with no scrollbar drawn, and centres the active tab once. Measured, not a
// breakpoint: three short tabs fit a phone and change nothing. Until then the
// list is exactly the desktop one; once it scrolls, its focus rings sit
// inside the triggers, since a scroller clips what sits outside it.
//
// Touch: every trigger takes a 44px tap (`nu-tap`, index.css), so the line
// variant draws its underline on `::before`, leaving `::after` to the tap.

import { cva, type VariantProps } from "class-variance-authority";
import { Tabs as TabsPrimitive } from "radix-ui";
import type * as React from "react";
import { createContext, useCallback, useContext, useLayoutEffect, useRef, useState } from "react";

import { cn } from "../../lib/utils";

// TabsList variants own the container chrome. Trigger active-state visuals
// are keyed off `data-variant` on the list so triggers stay a single component.
const tabsListVariants = cva(
	[
		"group/tabs-list inline-flex max-w-full items-center text-text-secondary",
		"data-[overflow]:overflow-x-auto data-[overflow]:overscroll-x-contain data-[overflow]:scrollbar-none",
	].join(" "),
	{
		variants: {
			variant: {
				line: [
					"border-b border-border-subtle gap-1",
					// A scroller clips at its border, and the active underline
					// overlaps it: the line moves inside, the same pixel.
					"data-[overflow]:border-b-0 data-[overflow]:pb-px",
					"data-[overflow]:shadow-[inset_0_-1px_0_var(--color-border-subtle)]",
				].join(" "),
				pill: "gap-1",
				segmented:
					"bg-bg-press border border-border-default rounded-md p-1 gap-1",
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
		"cursor-default",
		"transition-colors duration-fast ease-out",
		"disabled:pointer-events-none disabled:opacity-50",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"data-[state=active]:text-text-primary",
		"hover:text-text-primary",
		"[&_svg]:pointer-events-none [&_svg]:shrink-0",
		"nu-tap",
		// In a list that scrolls the ring would be clipped, so it sits inside.
		"group-data-[overflow]/tabs-list:focus-visible:ring-inset group-data-[overflow]/tabs-list:focus-visible:ring-offset-0",
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
		"data-[state=active]:before:absolute data-[state=active]:before:left-0",
		"data-[state=active]:before:right-0 data-[state=active]:before:-bottom-px",
		"data-[state=active]:before:h-0.5 data-[state=active]:before:bg-accent",
		"data-[state=active]:before:content-['']",
		"data-[state=active]:before:transition-transform data-[state=active]:before:duration-base data-[state=active]:before:ease-in-out",
	].join(" "),
	pill: [
		"rounded-md",
		"data-[state=active]:bg-bg-press data-[state=active]:text-text-primary",
	].join(" "),
	segmented: [
		"rounded-sm",
		"data-[state=active]:bg-bg-surface data-[state=active]:text-text-primary",
		"data-[state=active]:shadow-raised",
	].join(" "),
} as const;

type TabsVariant = "line" | "pill" | "segmented";

// The list's flavor, read by its triggers so they match without repeating it.
const TabsVariantContext = createContext<TabsVariant>("line");

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

/**
 * Whether a list's tabs run past its edge, kept current as the list, a tab
 * or the set of tabs changes size. `scrollWidth` counts the overflow whether
 * or not the list scrolls yet, so the answer never feeds back on itself.
 * The first time it runs over, the active tab is centred.
 */
function useOverflowX(forwarded?: React.Ref<HTMLDivElement>) {
	const [el, setEl] = useState<HTMLDivElement | null>(null);
	const [over, setOver] = useState(false);
	const fwd = useRef(forwarded);
	fwd.current = forwarded;
	const ref = useCallback((node: HTMLDivElement | null) => {
		setEl(node);
		const r = fwd.current;
		if (typeof r === "function") r(node);
		else if (r) (r as React.RefObject<HTMLDivElement | null>).current = node;
	}, []);
	useLayoutEffect(() => {
		if (!el || typeof ResizeObserver === "undefined") return;
		const measure = () => setOver(el.scrollWidth > el.clientWidth + 1);
		const sizes = new ResizeObserver(measure);
		const watch = () => {
			sizes.disconnect();
			sizes.observe(el);
			for (const tab of el.children) sizes.observe(tab);
			measure();
		};
		watch();
		const tabs = new MutationObserver(watch);
		tabs.observe(el, { childList: true });
		return () => {
			sizes.disconnect();
			tabs.disconnect();
		};
	}, [el]);
	useLayoutEffect(() => {
		const active = over ? el?.querySelector<HTMLElement>('[data-state="active"]') : null;
		if (!el || !active) return;
		// By hand: scrollIntoView would scroll the page too.
		const box = el.getBoundingClientRect();
		const tab = active.getBoundingClientRect();
		el.scrollLeft += tab.left - box.left - (box.width - tab.width) / 2;
	}, [el, over]);
	return { ref, over };
}

export interface TabsListProps
	extends React.ComponentProps<typeof TabsPrimitive.List>,
		VariantProps<typeof tabsListVariants> {}

export function TabsList({
	className,
	variant,
	ref,
	...props
}: TabsListProps) {
	const { ref: listRef, over } = useOverflowX(ref);
	return (
		<TabsVariantContext.Provider value={variant ?? "line"}>
			<TabsPrimitive.List
				ref={listRef}
				data-slot="tabs-list"
				data-variant={variant ?? "line"}
				data-overflow={over ? "" : undefined}
				className={cn(tabsListVariants({ variant }), className)}
				{...props}
			/>
		</TabsVariantContext.Provider>
	);
}

export interface TabsTriggerProps
	extends React.ComponentProps<typeof TabsPrimitive.Trigger>,
		VariantProps<typeof tabsTriggerVariants> {
	variant?: TabsVariant;
}

// Trigger takes an explicit `variant` too so consumers can render one trigger
// with a different active treatment, but the common case leaves it undefined
// and reads the parent list flavor from context.
export function TabsTrigger({
	className,
	size,
	variant,
	...props
}: TabsTriggerProps) {
	const listVariant = useContext(TabsVariantContext);
	return (
		<TabsPrimitive.Trigger
			data-slot="tabs-trigger"
			className={cn(
				tabsTriggerVariants({ size }),
				triggerVariantClass[variant ?? listVariant],
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
