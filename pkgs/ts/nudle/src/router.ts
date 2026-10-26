// Routing: the kit Router on History, with the pages read off the tree.
//
// A page is a root-level node of type "Page" whose `route` and `label` are
// declared props, so they ride the chain onto the node at boot and stay
// there. The page router's branches are those routes, matched exactly on
// the pathname (the kit's `matchRoute`), so the query is free for the page:
// `/feed?x=1` is the feed page. Nothing here writes history and nothing
// depends on a HistoryRef node existing: where the page is comes from
// History, which hears every move.
//
// No match is the not-found fallback, with one exception: the bare "/" of an
// app that declares no page there is its front door, and shows the first
// page. Any other unmatched path shows not-found, rather than some page the
// URL does not name.
//
// Every hook here returns a string, a sentinel or a shallow-compared string
// list on purpose: the shell re-renders when the active page changes and not
// when something deep inside one of them does.

import type { TreeNode } from "@nustackdev/ui-core";
import { matchRoute, trimSlash, useEntry, useTree } from "@nustackdev/ui-kit";
import { useMemo } from "react";
import { useShallow } from "zustand/react/shallow";

export const PAGE_TYPE = "Page";

/** What `useActivePage` answers when the URL names no page. */
export const NOT_FOUND = Symbol("not-found");

const NONE: string[] = [];

/** Every root-level child, in the order it was written. */
export function useRootSegments(): string[] {
	return useTree(
		useShallow((s) => {
			if (!s.root.children.size) return NONE;
			return [...s.root.children.keys()];
		}),
	);
}

function pageSegments(root: TreeNode): string[] {
	const out: string[] = [];
	for (const [segment, node] of root.children) {
		if (node.type === PAGE_TYPE) out.push(segment);
	}
	return out.length ? out : NONE;
}

/** The pages, in declaration order. Empty for a single-page app. */
export function usePageSegments(): string[] {
	return useTree(useShallow((s) => pageSegments(s.root)));
}

/** A page's route: its declared `route`, else its segment as a path. */
export function routeOf(segment: string, route: unknown): string {
	return route == null || route === "" ? `/${segment}` : String(route);
}

/** Every page's route, in declaration order, as `segment\troute` pairs (shallow-comparable). */
function usePageRoutes(): string[] {
	return useTree(
		useShallow((s) => {
			const out: string[] = [];
			for (const [segment, node] of s.root.children) {
				if (node.type === PAGE_TYPE) out.push(`${segment}\t${routeOf(segment, node.props.route)}`);
			}
			return out.length ? out : NONE;
		}),
	);
}

type PageBranch = { path: string; segment: string };

/**
 * The page `pathname` names among `pages` (segment and route, in
 * declaration order): its segment, the first page for a bare "/" no page
 * claims, NOT_FOUND for anything else, and null with no pages at all.
 */
export function pageFor(
	pages: readonly PageBranch[],
	pathname: string,
): string | typeof NOT_FOUND | null {
	if (pages.length === 0) return null;
	const hit = matchRoute(pages, {
		url: pathname,
		path: pathname,
		query: {},
		hash: "",
		state: null,
	});
	if (hit) return hit.branch.segment;
	return trimSlash(pathname) === "/" ? pages[0].segment : NOT_FOUND;
}

/** The page to show, re-matched on every History move. */
export function useActivePage(): string | typeof NOT_FOUND | null {
	const pairs = usePageRoutes();
	const branches = useMemo(
		() =>
			pairs.map((pair) => {
				const [segment, path] = pair.split("\t");
				return { segment, path };
			}),
		[pairs],
	);
	const { path } = useEntry();
	return pageFor(branches, path);
}
