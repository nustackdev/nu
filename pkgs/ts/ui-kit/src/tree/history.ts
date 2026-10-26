// History: the one writer of the browser's history, and the one place that
// says where the page is.
//
// An entry is a URL plus state, a structured-clone-safe value that rides
// with the entry and is not in the URL (nuspace keeps its pane layout
// there). Every move goes through `History`: nothing else in the kit, and
// nothing in a host built on it, calls `pushState` or `replaceState`. So
// every move is heard, synchronously, by everything that subscribed:
//   - push and replace announce themselves the moment they land
//   - back, forward and go land later, as a popstate, and are announced then
//   - a move the browser makes on its own (the user's back button, a
//     fragment link) is a popstate too
//
// Each move carries a `source`: "program" for one some code asked for
// (push, replace, or a popstate a back / forward / go of ours caused) and
// "browser" for the rest. A caller can tag its move with an `origin`, any
// value, and the move announces it, so a listener can tell its own moves
// from everyone else's (the HistoryRef node does exactly that, to never echo
// a move the server asked for). A popstate is matched to the traversal that
// caused it in call order; a traversal that leads nowhere (forward at the
// end of the stack) fires no popstate, so its tag expires after
// TRAVERSE_WINDOW_MS rather than tagging some later move of the user's.
//
// A push or replace to the entry the page is already on, same URL and same
// state, is no move: no entry, no announcement. A URL on another origin is
// not a history move at all: push assigns the location, replace replaces
// it, and the page leaves.
//
// Hosts cannot swap this. A host with its own router listens (see
// ./router), it does not take over the writing.

import { useSyncExternalStore } from "react";
import { resolveHref, sameOrigin } from "../lib/anchor";
import { parseQuery, type Query } from "./query";

/** Where the page is: the URL, its parts, and the state that rides with it. */
export type Entry = {
	/** Path, query and hash: "/movie?id=42#cast". */
	url: string;
	/** "/movie" */
	path: string;
	/** The query as a dict: {id: "42"}. */
	query: Query;
	/** "#cast", or "" for none. */
	hash: string;
	/** The entry's state, or null for none. */
	state: unknown;
};

/** What a move did: added an entry, replaced the current one, or traversed. */
export type MoveKind = "push" | "replace" | "pop";

/** One move, as a subscriber hears it. */
export type Move = {
	kind: MoveKind;
	/** "program" when some code asked for it, "browser" when the browser moved by itself. */
	source: "program" | "browser";
	/** The tag the caller passed, if any. Always undefined for a browser move. */
	origin: unknown;
	/** Where the page is now. */
	entry: Entry;
	/** Where it was. */
	previous: Entry;
};

/** How a caller tags its move. */
export type MoveOptions = { origin?: unknown };

/** How long a back / forward / go waits for its popstate before its tag lapses. */
export const TRAVERSE_WINDOW_MS = 1000;

type Listener = (move: Move) => void;

const listeners = new Set<Listener>();

// The entry, rebuilt only when the address or the state object changes, so a
// React store sees one stable snapshot per entry.
let cached: { href: string; state: unknown; entry: Entry } | null = null;

function readEntry(): Entry {
	const href = window.location.href;
	const state = window.history.state ?? null;
	if (cached && cached.href === href && cached.state === state) return cached.entry;
	const { pathname, search, hash } = window.location;
	const entry: Entry = {
		url: pathname + search + hash,
		path: pathname,
		query: parseQuery(search),
		hash,
		state,
	};
	cached = { href, state, entry };
	return entry;
}

// Traversals of ours still waiting for their popstate, oldest first.
const pending: { origin: unknown; at: number }[] = [];

function announce(move: Move): void {
	for (const fn of [...listeners]) {
		try {
			fn(move);
		} catch (err) {
			console.error("History listener failed", err);
		}
	}
}

let last: Entry | null = null;

function onPopState(): void {
	const now = Date.now();
	while (pending.length && now - pending[0].at > TRAVERSE_WINDOW_MS) pending.shift();
	const own = pending.shift();
	const previous = last ?? readEntry();
	const entry = readEntry();
	last = entry;
	announce({
		kind: "pop",
		source: own ? "program" : "browser",
		origin: own?.origin,
		entry,
		previous,
	});
}

let listening = false;

function listen(): void {
	if (listening || typeof window === "undefined") return;
	listening = true;
	last = readEntry();
	window.addEventListener("popstate", onPopState);
}

/** Structural equality for structured-clone-safe values, by identity for the rest. */
function sameState(a: unknown, b: unknown): boolean {
	if (Object.is(a, b)) return true;
	if (a == null || b == null) return (a ?? null) === (b ?? null);
	if (typeof a !== "object" || typeof b !== "object") return false;
	if (Array.isArray(a)) {
		if (!Array.isArray(b) || a.length !== b.length) return false;
		return a.every((v, i) => sameState(v, b[i]));
	}
	if (Array.isArray(b)) return false;
	const pa = Object.getPrototypeOf(a);
	if ((pa !== Object.prototype && pa !== null) || Object.getPrototypeOf(b) !== pa) return false;
	const ka = Object.keys(a);
	const kb = Object.keys(b);
	if (ka.length !== kb.length) return false;
	const ob = b as Record<string, unknown>;
	return ka.every(
		(k) => Object.hasOwn(ob, k) && sameState((a as Record<string, unknown>)[k], ob[k]),
	);
}

function write(kind: "push" | "replace", url: string, state: unknown, opts?: MoveOptions): boolean {
	listen();
	const target = resolveHref(url);
	if (!target) return false;
	if (target.origin !== window.location.origin) {
		if (kind === "push") window.location.assign(target.href);
		else window.location.replace(target.href);
		return false;
	}
	const previous = readEntry();
	const next = target.pathname + target.search + target.hash;
	const nextState = state === undefined ? null : state;
	if (next === previous.url && sameState(nextState, previous.state)) return false;
	if (kind === "push") window.history.pushState(nextState, "", next);
	else window.history.replaceState(nextState, "", next);
	const entry = readEntry();
	last = entry;
	announce({ kind, source: "program", origin: opts?.origin, entry, previous });
	return true;
}

function traverse(delta: number, opts?: MoveOptions): void {
	listen();
	if (delta === 0) return;
	pending.push({ origin: opts?.origin, at: Date.now() });
	window.history.go(delta);
}

/** The browser's history, the only way the kit moves the page. */
export const History = {
	/**
	 * A new entry at `url` with `state`. Relative URLs resolve against the
	 * page. Returns whether the page moved: false for the entry it is on
	 * already, and for a URL on another origin (which leaves the page).
	 */
	push(url: string, state?: unknown, opts?: MoveOptions): boolean {
		return write("push", url, state, opts);
	},
	/** `url` with `state` in place of the current entry. Returns whether the page moved. */
	replace(url: string, state?: unknown, opts?: MoveOptions): boolean {
		return write("replace", url, state, opts);
	},
	/** One entry back. Lands later, as a "pop" move. */
	back(opts?: MoveOptions): void {
		traverse(-1, opts);
	},
	/** One entry forward. Lands later, as a "pop" move. */
	forward(opts?: MoveOptions): void {
		traverse(1, opts);
	},
	/** `delta` entries along the stack. Lands later, as a "pop" move. */
	go(delta: number, opts?: MoveOptions): void {
		traverse(delta, opts);
	},
	/** Where the page is now. The same object until the entry changes. */
	current(): Entry {
		return readEntry();
	},
	/** Hear every move, synchronously. Returns the unsubscribe. */
	subscribe(fn: (move: Move) => void): () => void {
		listen();
		listeners.add(fn);
		return () => {
			listeners.delete(fn);
		};
	},
};

const SERVER_ENTRY: Entry = { url: "/", path: "/", query: {}, hash: "", state: null };

function subscribeStore(onChange: () => void): () => void {
	return History.subscribe(onChange);
}

/** The current entry, re-rendering on every move. */
export function useEntry(): Entry {
	return useSyncExternalStore(subscribeStore, readEntry, () => SERVER_ENTRY);
}

function readPath(): string {
	return readEntry().path;
}

/** The page's pathname, re-rendering only when it changes. */
export function usePathname(): string {
	return useSyncExternalStore(subscribeStore, readPath, () => "/");
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

/** A pathname without its trailing slash, "/" kept as is. */
export function trimSlash(p: string): string {
	return p.length > 1 && p.endsWith("/") ? p.slice(0, -1) : p;
}
