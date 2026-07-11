// Breadcrumb primitive. Hierarchical path navigation.
//
// Design refs:
//   primitives.md    §Breadcrumb (compound parts, sizes, variants)
//   palette.md       §2.2 text tiers, §2.4 accent for links
//   a11y.md          §4 <nav aria-label="Breadcrumb"><ol>
//
// Compound shape (BreadcrumbList/Item/Link/Page/Separator/Ellipsis) matches
// shadcn's Breadcrumb pattern so consumer sites feel familiar. `Slot.Root` on
// BreadcrumbLink lets a router <Link> take over the anchor node without a
// wrapper.

import { Slot as SlotPrimitive } from "radix-ui";
import { ChevronRight, MoreHorizontal } from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";

export function Breadcrumb({
	className,
	...props
}: React.HTMLAttributes<HTMLElement>) {
	return (
		<nav
			aria-label="Breadcrumb"
			data-slot="breadcrumb"
			className={cn(className)}
			{...props}
		/>
	);
}

export function BreadcrumbList({
	className,
	...props
}: React.OlHTMLAttributes<HTMLOListElement>) {
	return (
		<ol
			data-slot="breadcrumb-list"
			className={cn(
				"flex flex-wrap items-center gap-1.5 text-sm text-text-secondary",
				className,
			)}
			{...props}
		/>
	);
}

export function BreadcrumbItem({
	className,
	...props
}: React.LiHTMLAttributes<HTMLLIElement>) {
	return (
		<li
			data-slot="breadcrumb-item"
			className={cn("inline-flex items-center gap-1.5", className)}
			{...props}
		/>
	);
}

export interface BreadcrumbLinkProps
	extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
	asChild?: boolean;
}

export function BreadcrumbLink({
	className,
	asChild = false,
	...props
}: BreadcrumbLinkProps) {
	const Comp = asChild ? SlotPrimitive.Root : "a";
	return (
		<Comp
			data-slot="breadcrumb-link"
			className={cn(
				"text-text-secondary transition-colors duration-fast ease-out",
				"hover:text-accent",
				"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas rounded-sm",
				className,
			)}
			{...props}
		/>
	);
}

// Current page: rendered as non-link, aria-current="page". Reads as the terminal
// crumb in the trail.
export function BreadcrumbPage({
	className,
	...props
}: React.HTMLAttributes<HTMLSpanElement>) {
	return (
		<span
			role="link"
			aria-disabled="true"
			aria-current="page"
			data-slot="breadcrumb-page"
			className={cn("text-text-primary font-medium", className)}
			{...props}
		/>
	);
}

export interface BreadcrumbSeparatorProps
	extends React.HTMLAttributes<HTMLLIElement> {
	children?: React.ReactNode;
}

export function BreadcrumbSeparator({
	className,
	children,
	...props
}: BreadcrumbSeparatorProps) {
	return (
		<li
			role="presentation"
			aria-hidden="true"
			data-slot="breadcrumb-separator"
			className={cn(
				"inline-flex items-center text-text-muted [&>svg]:size-3.5",
				className,
			)}
			{...props}
		>
			{children ?? <ChevronRight />}
		</li>
	);
}

// Ellipsis condenses middle crumbs. Non-interactive by default; a Popover
// integration can layer on later per primitives.md §Breadcrumb.
export function BreadcrumbEllipsis({
	className,
	...props
}: React.HTMLAttributes<HTMLSpanElement>) {
	return (
		<span
			role="presentation"
			aria-hidden="true"
			data-slot="breadcrumb-ellipsis"
			className={cn(
				"inline-flex size-4 items-center justify-center text-text-muted",
				className,
			)}
			{...props}
		>
			<MoreHorizontal className="size-3.5" />
			<span className="sr-only">More</span>
		</span>
	);
}
