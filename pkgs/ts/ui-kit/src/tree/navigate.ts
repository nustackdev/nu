// The navigator: how the kit moves the page, and the one seam a host swaps.
//
// `NavRef` never touches `window.history` itself. It asks the active
// navigator, and the default one is plain history: push and replace call
// `pushState` / `replaceState`, back and forward call the history methods,
// and a change is a `popstate`. That is what a page that owns its whole URL
// wants, and it is the behaviour NavRef always had.
//
// A host with its own router installs a navigator instead (`setNavigator`),
// so a write from the server moves whatever that router draws, and a move the
// router makes reaches the server as a change. Whatever the host leaves out
// falls back to the default, so a router that only cares about push and
// replace installs those two and nothing else.
//
// Where the page is, for anything that follows it (NavRef mirroring the uri,
// a NavItem lighting up for its page), is one source: `subscribeLocation`.
// Following the page needs to hear about every move, and a plain pushState
// fires no event. So the location is re-read on the navigator's own moves,
// on the Navigation API's currententrychange where the browser has it
// (which pushState does fire), and on every tree change, which is when a
// NavRef write or a host's routing has just redrawn something. Each read is
// one string compare.

import { useSyncExternalStore } from "react";
import { resolveHref, sameOrigin } from "../lib/anchor";
import { tree } from "./store";

/** How the page moves. Every member is optional on install. */
export type Navigator = {
	/** Go to `uri`, a new history entry. */
	push: (uri: string) => void;
	/** Go to `uri` in place of the current entry. */
	replace: (uri: string) => void;
	back: () => void;
	forward: () => void;
	/** Where the page is now: path, query and hash. */
	current: () => string;
	/** Hear every move the page makes. Returns the unsubscribe. */
	subscribe: (onMove: () => void) => () => void;
};

function locationUri(): string {
	return window.location.pathname + window.location.search + window.location.hash;
}

/** Plain browser history. What the kit uses until a host installs its own. */
export const historyNavigator: Navigator = {
	push: (uri) => {
		// No duplicate entries for the uri the page is already on.
		if (uri !== locationUri()) window.history.pushState({}, "", uri);
	},
	replace: (uri) => {
		if (uri !== locationUri()) window.history.replaceState({}, "", uri);
	},
	back: () => window.history.back(),
	forward: () => window.history.forward(),
	current: locationUri,
	subscribe: (onMove) => {
		window.addEventListener("popstate", onMove);
		return () => window.removeEventListener("popstate", onMove);
	},
};

let active: Navigator = historyNavigator;

/**
 * Install the host's navigator, over the default member by member. `null`
 * puts the default back. Install before the first write can land.
 */
export function setNavigator(navigator: Partial<Navigator> | null): void {
	active = navigator ? { ...historyNavigator, ...navigator } : historyNavigator;
}

/** The navigator in force. Read at call time, never cached. */
export function activeNavigator(): Navigator {
	return active;
}

/**
 * Hear every move the page may have made: the navigator's, the browser's
 * own, and every tree change. Returns the unsubscribe. A listener re-reads
 * the location and compares, since most of these are not moves.
 */
export function subscribeLocation(onChange: () => void): () => void {
	const unsubscribeNavigator = active.subscribe(onChange);
	const navigation = (window as unknown as { navigation?: EventTarget }).navigation;
	navigation?.addEventListener("currententrychange", onChange);
	const unsubscribeTree = tree.subscribe(onChange);
	return () => {
		unsubscribeNavigator();
		navigation?.removeEventListener("currententrychange", onChange);
		unsubscribeTree();
	};
}

function readPathname(): string {
	return resolveHref(active.current())?.pathname ?? window.location.pathname;
}

/** The page's pathname, kept current across every move `subscribeLocation` hears. */
export function usePathname(): string {
	return useSyncExternalStore(subscribeLocation, readPathname, () => "/");
}

/** Whether `href` names the page at `pathname`, or one above it unless `exact`. */
export function matchesPath(href: string, pathname: string, exact: boolean): boolean {
	if (!sameOrigin(href)) return false;
	const target = resolveHref(href);
	if (!target) return false;
	const want = trimSlash(target.pathname);
	const here = trimSlash(pathname);
	if (want === here) return true;
	if (exact || want === "/") return false;
	return here.startsWith(`${want}/`);
}

function trimSlash(p: string): string {
	return p.length > 1 && p.endsWith("/") ? p.slice(0, -1) : p;
}
