// Card primitive. Bounded content surface with optional header/footer/action.
// Design refs:
//   primitives.md    §Card (compound parts, variants, sizes, states)
//   palette.md       §2.1 backgrounds, §2.3 borders
//   space-radius.md  §Density Card (pad 12 / 16 / 24, gap 8 / 12 / 16)
//   motion.md        §3 Button hover row (interactive borrows the same fast+ease-out)
//   a11y.md          §1 focus-ring for interactive variant
//
// Article-flavored surface. Panel is the toolbar-flavored sibling.

import { cva, type VariantProps } from "class-variance-authority";
import { Slot as SlotPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const cardVariants = cva(
	[
		"flex flex-col rounded-lg",
		"transition-colors duration-fast ease-out",
	].join(" "),
	{
		variants: {
			variant: {
				default: "bg-bg-surface border border-border-default",
				elevated:
					"bg-bg-elevated border border-border-default shadow-sm",
				sunken: "bg-bg-sunken border border-transparent",
				outline: "bg-transparent border border-border-default",
			},
			size: {
				// gap between children of Card matches space-radius §Density Card.
				sm: "gap-2",
				md: "gap-3",
				lg: "gap-4",
			},
			interactive: {
				true: [
					"cursor-pointer",
					"hover:border-border-strong",
					"focus-ring",
				].join(" "),
				false: "",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
			interactive: false,
		},
	},
);

// Header / Content / Footer inherit the outer pad through a CSS var so we can
// swap px in Header + Footer without redeclaring size logic.
const cardPadStyles = {
	sm: "[--card-pad:0.75rem]", // 12
	md: "[--card-pad:1rem]", // 16
	lg: "[--card-pad:1.5rem]", // 24
} as const;

export interface CardProps
	extends React.HTMLAttributes<HTMLDivElement>,
		VariantProps<typeof cardVariants> {
	asChild?: boolean;
}

export function Card({
	className,
	variant,
	size,
	interactive,
	asChild = false,
	...props
}: CardProps) {
	const Comp = asChild ? SlotPrimitive.Root : "div";
	const padClass = cardPadStyles[size ?? "md"];
	return (
		<Comp
			data-slot="card"
			data-size={size ?? "md"}
			className={cn(
				cardVariants({ variant, size, interactive }),
				padClass,
				className,
			)}
			{...props}
		/>
	);
}

// Header uses a two-column grid when a `CardAction` sits inside it, so the
// action rides top-right without extra flex plumbing at the call site.
export function CardHeader({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="card-header"
			className={cn(
				"grid auto-rows-min items-start gap-1",
				"has-[[data-slot=card-action]]:grid-cols-[1fr_auto]",
				"px-[var(--card-pad)] pt-[var(--card-pad)]",
				className,
			)}
			{...props}
		/>
	);
}

export function CardTitle({
	className,
	...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
	return (
		<h3
			data-slot="card-title"
			className={cn(
				"text-lg font-semibold leading-none text-text-primary",
				className,
			)}
			{...props}
		/>
	);
}

export function CardDescription({
	className,
	...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
	return (
		<p
			data-slot="card-description"
			className={cn("text-sm text-text-secondary", className)}
			{...props}
		/>
	);
}

// Right-rail slot inside CardHeader. Kept as its own component so the
// `has-[[data-slot=card-action]]` selector on CardHeader picks it up.
export function CardAction({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="card-action"
			className={cn(
				"col-start-2 row-span-2 row-start-1 self-start justify-self-end",
				className,
			)}
			{...props}
		/>
	);
}

export function CardContent({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="card-content"
			className={cn("px-[var(--card-pad)]", className)}
			{...props}
		/>
	);
}

export function CardFooter({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="card-footer"
			className={cn(
				"flex items-center gap-2",
				"px-[var(--card-pad)] pb-[var(--card-pad)]",
				className,
			)}
			{...props}
		/>
	);
}

export { cardVariants };
