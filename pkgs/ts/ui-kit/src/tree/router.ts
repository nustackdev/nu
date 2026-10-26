// Router: match the current History entry against a list of branches.
//
// A router only listens. It never writes history, never remembers what it
// showed and never mounts anything: it says which branch the entry is on,
// and the host draws that branch. nudle's page router and nuspace's pane
// router are hosts of this kind, built on it.
//
// A branch is one of:
//   - a pathname, "/feed": the entry's path is that, exactly (a trailing
//     slash aside, so "/feed/" is "/feed"). The query and hash are free.
//   - {path: "/feed", ...}: the same, with whatever else the host hangs on it
//   - {match: (entry) => ..., ...}: the host's own test. True, or a params
//     dict, is a match; false, null or undefined is not.
// The first branch that matches wins. No branch matching is the fallback.

import { useMemo } from "react";
import { type Entry, trimSlash, useEntry } from "./history";

/** What a matching branch yields besides itself. */
export type RouteParams = Record<string, string>;

/** A branch: a pathname, or an object with a `path` or a `match`. */
export type RouteBranch =
	| string
	| { path: string; match?: never }
	| { match: (entry: Entry) => boolean | RouteParams | null | undefined; path?: string };

/** The branch an entry is on. */
export type RouteMatch<B> = {
	branch: B;
	/** The branch's place in the list. */
	index: number;
	/** What a `match` returned, or {} for a path branch. */
	params: RouteParams;
};

function test(branch: RouteBranch, entry: Entry): RouteParams | null {
	if (typeof branch === "string") return trimSlash(branch) === trimSlash(entry.path) ? {} : null;
	if (typeof branch.match === "function") {
		const hit = branch.match(entry);
		if (hit === true) return {};
		if (hit && typeof hit === "object") return hit;
		return null;
	}
	return trimSlash(branch.path ?? "") === trimSlash(entry.path) ? {} : null;
}

/** The first branch `entry` is on, or null for none. Pure. */
export function matchRoute<B extends RouteBranch>(
	branches: readonly B[],
	entry: Entry,
): RouteMatch<B> | null {
	for (let index = 0; index < branches.length; index++) {
		const params = test(branches[index], entry);
		if (params) return { branch: branches[index], index, params };
	}
	return null;
}

/**
 * The branch the page is on, re-matched on every History move. With no
 * match, `fallback` (null when not given).
 */
export function useRoute<B extends RouteBranch, F = null>(
	branches: readonly B[],
	fallback?: F,
): RouteMatch<B> | F {
	const entry = useEntry();
	const match = useMemo(() => matchRoute(branches, entry), [branches, entry]);
	return match ?? ((fallback ?? null) as F);
}
