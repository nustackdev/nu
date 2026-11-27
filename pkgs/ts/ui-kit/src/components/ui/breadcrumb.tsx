// Breadcrumb primitive. Hierarchical path navigation.
//
// Design refs:
//   primitives.md    §Breadcrumb (compound parts, sizes, variants)
//   palette.md       text tiers, accent for links
//   a11y.md          §4 <nav aria-label="Breadcrumb"><ol>
//
// Compound shape (BreadcrumbList/Item/Link/Page/Separator/Ellipsis) matches
// shadcn's Breadcrumb pattern so consumer sites feel familiar. `Slot.Root` on
// BreadcrumbLink lets a router <Link> take over the anchor node without a
// wrapper.
//
// Narrow: the trail follows the room it has, not the screen. When a trail of
// four crumbs or more does not fit on one line where it sits (it would wrap,
// or overflow a list that does not wrap), it keeps the first, the parent and
// the current page and folds the rest into an ellipsis, so a phone and a
// strip column read "Home > ... > Parent > Page" on one line. The nav
// measures itself (a ResizeObserver on it, its list and its parent) and
// marks itself `data-fold`; CSS on the rendered items does the folding, so a
// trail built from Fragments folds as well as a flat one. It assumes the
// usual shape: crumbs and separators taking turns, a crumb first and last.
// The nav sizes like any element: in a row it is as wide as its crumbs.

import { Slot as SlotPrimitive } from "radix-ui";
import { ChevronRight, MoreHorizontal } from "lucide-react";
import type * as React from "react";
import { useLayoutEffect, useRef } from "react";

import { cn } from "../../lib/utils";

/** Items in a trail of four crumbs: crumbs and separators taking turns. */
const FOLD_ITEMS = 7;

/** Whether the trail's items wrap past one line or overflow the list. */
function crowded(list: HTMLElement): boolean {
	const first = list.firstElementChild;
	const last = list.lastElementChild;
	if (!first || !last) return false;
	if (list.scrollWidth > list.clientWidth + 1) return true;
	return last.getBoundingClientRect().top >= first.getBoundingClientRect().bottom;
}

/**
 * Keep `data-fold` on the nav while its whole trail does not fit. Each check
 * unfolds, measures and folds back in the same frame, so nothing flickers,
 * and so a fold lifts again once the room comes back.
 */
function useFold(nav: React.RefObject<HTMLElement | null>) {
	useLayoutEffect(() => {
		const el = nav.current;
		const list = el?.querySelector<HTMLElement>('[data-slot="breadcrumb-list"]');
		if (!el || !list || typeof ResizeObserver === "undefined") return;
		const check = () => {
			el.removeAttribute("data-fold");
			if (list.children.length >= FOLD_ITEMS && crowded(list)) el.setAttribute("data-fold", "");
		};
		const size = new ResizeObserver(check);
		size.observe(el);
		size.observe(list);
		if (el.parentElement) size.observe(el.parentElement);
		const crumbs = new MutationObserver(check);
		crumbs.observe(list, { childList: true });
		return () => {
			size.disconnect();
			crumbs.disconnect();
		};
	}, [nav]);
}

export function Breadcrumb({
	className,
	...props
}: React.HTMLAttributes<HTMLElement>) {
	const ref = useRef<HTMLElement>(null);
	useFold(ref);
	return (
		<nav
			ref={ref}
			aria-label="Breadcrumb"
			data-slot="breadcrumb"
			className={cn("group/breadcrumb", className)}
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
				// Folded (the nav's `data-fold`): drop every item between the
				// first separator and the parent's, and draw the ellipsis after
				// the first separator, so a separator follows it.
				"group-data-fold/breadcrumb:[&>li:nth-child(n+3):nth-last-child(n+5)]:hidden",
				"group-data-fold/breadcrumb:[&>li:nth-child(2)]:after:ms-1.5",
				"group-data-fold/breadcrumb:[&>li:nth-child(2)]:after:content-['…']",
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
				"cursor-default nu-tap",
				"hover:text-accent-text",
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
