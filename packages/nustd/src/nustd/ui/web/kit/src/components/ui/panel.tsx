// Panel primitive. Toolbar-flavored container, denser than Card.
// Design refs:
//   primitives.md    §Panel (compound parts, variants)
//   palette.md       §2.1 backgrounds, §2.3 borders
//   space-radius.md  §Density Panel (denser than Card: pad 8 / 12 / 16)
//
// Typical hosts: nudle right-side inspector, sidebar filters, toolbars. Cards
// host content; Panels host controls. The visual language is the same, the
// pad ladder is one step tighter and the header can stick to the top of a
// scroll container via `stickyHeader`.

import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "../../lib/utils";

const panelVariants = cva("flex flex-col rounded-lg", {
	variants: {
		variant: {
			default: "bg-bg-surface border border-border-default",
			sunken: "bg-bg-sunken border border-transparent",
			elevated:
				"bg-bg-elevated border border-border-default shadow-sm",
		},
		size: {
			sm: "gap-1.5",
			md: "gap-2",
			lg: "gap-3",
		},
	},
	defaultVariants: {
		variant: "default",
		size: "md",
	},
});

// Same technique as Card: outer size feeds children pad via a CSS var so
// PanelHeader / PanelContent / PanelFooter stay ignorant of the ladder.
const panelPadStyles = {
	sm: "[--panel-pad:0.5rem]", // 8
	md: "[--panel-pad:0.75rem]", // 12
	lg: "[--panel-pad:1rem]", // 16
} as const;

export interface PanelProps
	extends React.HTMLAttributes<HTMLDivElement>,
		VariantProps<typeof panelVariants> {}

export function Panel({
	className,
	variant,
	size,
	...props
}: PanelProps) {
	const padClass = panelPadStyles[size ?? "md"];
	return (
		<div
			data-slot="panel"
			data-size={size ?? "md"}
			className={cn(panelVariants({ variant, size }), padClass, className)}
			{...props}
		/>
	);
}

// `sticky` opts the header into `position: sticky` for scroll containers where
// the panel body scrolls but the header should pin to the top (nudle inspector).
export interface PanelHeaderProps
	extends React.HTMLAttributes<HTMLDivElement> {
	sticky?: boolean;
}

export function PanelHeader({
	className,
	sticky = false,
	...props
}: PanelHeaderProps) {
	return (
		<div
			data-slot="panel-header"
			className={cn(
				"flex items-center gap-2",
				"px-[var(--panel-pad)] pt-[var(--panel-pad)]",
				sticky &&
					"sticky top-0 z-10 bg-inherit border-b border-border-subtle pb-[var(--panel-pad)]",
				className,
			)}
			{...props}
		/>
	);
}

export function PanelTitle({
	className,
	...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
	return (
		<h3
			data-slot="panel-title"
			className={cn(
				"text-base font-semibold leading-none text-text-primary",
				className,
			)}
			{...props}
		/>
	);
}

export function PanelDescription({
	className,
	...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
	return (
		<p
			data-slot="panel-description"
			className={cn("text-sm text-text-secondary", className)}
			{...props}
		/>
	);
}

export function PanelContent({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="panel-content"
			className={cn("px-[var(--panel-pad)]", className)}
			{...props}
		/>
	);
}

export function PanelFooter({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="panel-footer"
			className={cn(
				"flex items-center gap-2",
				"px-[var(--panel-pad)] pb-[var(--panel-pad)]",
				className,
			)}
			{...props}
		/>
	);
}

export { panelVariants };
