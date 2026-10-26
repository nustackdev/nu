// AnchorCatcher: how a click on a plain <a href> becomes an in-app move.
//
// Every kit link is a real anchor whose href is where it goes, so the
// browser's own handling (open in a new tab, copy link) always works. A host
// mounts the catcher on its root, and it turns the clicks that are the
// app's to handle into `(href, gesture)` for the host's rule:
//
//   - an `a[href]` the event reached, not already handled (defaultPrevented)
//   - same origin as the page, target empty or `_self`, no `download`
//   - not inside an editable region (a link in an editor is for editing)
//   - the primary button. Cmd, Ctrl and Shift are always the browser's, and a
//     middle or right click never arrives as a click at all.
//   - Option / Alt is passed on as gesture "alt", everything else qualifying
//     is "plain"
//
// The rule answers true when it handled the link (the catcher then cancels
// the browser's navigation) and false to leave it native. The default rule
// pushes a plain one through History and leaves "alt" native.
//
// Keys: Enter on a focused link fires a click in every browser, so plain
// Enter is the click path above. Option+Enter is not one gesture across
// browsers (some fire a click carrying the modifier, some take it as their
// own "download the link" with no click to catch), so the catcher does not
// wait for a click: a keydown of Option+Enter on the link itself goes to the
// rule as "alt". When the rule takes it, the keydown's
// default (and any click it would fire) is cancelled; when it does not, the
// click that may follow is let through untouched, so the rule is asked once
// per gesture. Nothing else is listened for: no key the catcher does not
// handle is ever blocked, and there are no shortcuts.
//
// The href the rule gets is the app's own form, path, query and hash
// ("/movie?id=42"), not the absolute URL the anchor resolves to. A link to a
// fragment of the page it is on ("#cast") is left native, so the browser
// scrolls to it; History hears the move as a browser popstate.

import { type ReactNode, type RefObject, useEffect, useRef } from "react";
import { sameOrigin } from "../lib/anchor";
import { History } from "./history";

/** How the link was activated: plainly, or with Option / Alt held. */
export type Gesture = "plain" | "alt";

/**
 * The host's rule for an in-app link. True when it handled the move (the
 * browser's navigation is cancelled), false to leave the link native.
 */
export type AnchorRule = (
	href: string,
	gesture: Gesture,
	anchor: HTMLAnchorElement,
	event: MouseEvent | KeyboardEvent,
) => boolean;

/** Plain: a push through History. Alt: native. */
export const defaultAnchorRule: AnchorRule = (href, gesture) => {
	if (gesture !== "plain") return false;
	History.push(href);
	return true;
};

function anchorOf(target: EventTarget | null, root: HTMLElement): HTMLAnchorElement | null {
	if (!(target instanceof Element)) return null;
	const a = target.closest("a[href]");
	if (!(a instanceof HTMLAnchorElement) || !root.contains(a)) return null;
	return a;
}

/** The app's own form of the anchor's href, or null when it is not the app's to route. */
function inAppHref(a: HTMLAnchorElement): string | null {
	const target = a.getAttribute("target");
	if (target && target !== "_self") return null;
	if (a.hasAttribute("download")) return null;
	if (a.isContentEditable || a.closest("[contenteditable]:not([contenteditable='false'])"))
		return null;
	const raw = a.getAttribute("href") ?? "";
	if (!sameOrigin(raw)) return null;
	const url = new URL(a.href);
	const here = window.location;
	if (url.hash !== "" && url.pathname === here.pathname && url.search === here.search) return null;
	return url.pathname + url.search + url.hash;
}

/**
 * Route the in-app links under `root` through `rule`. Returns the cleanup.
 * One catcher per root: a catcher inside another hears the same clicks.
 */
export function catchAnchors(root: HTMLElement, rule: AnchorRule = defaultAnchorRule): () => void {
	// The anchor whose Option+Enter the rule declined, so the click the key
	// may fire next is the browser's.
	let declined: HTMLAnchorElement | null = null;

	const onClick = (e: MouseEvent) => {
		if (e.defaultPrevented || e.button !== 0) return;
		if (e.metaKey || e.ctrlKey || e.shiftKey) return;
		const a = anchorOf(e.target, root);
		if (!a) return;
		if (a === declined) return;
		const href = inAppHref(a);
		if (href === null) return;
		if (rule(href, e.altKey ? "alt" : "plain", a, e)) e.preventDefault();
	};

	const onKeyDown = (e: KeyboardEvent) => {
		if (e.defaultPrevented || e.key !== "Enter" || e.isComposing) return;
		if (!e.altKey || e.metaKey || e.ctrlKey || e.shiftKey) return;
		const a = e.target;
		if (!(a instanceof HTMLAnchorElement) || !a.hasAttribute("href") || !root.contains(a)) return;
		const href = inAppHref(a);
		if (href === null) return;
		if (rule(href, "alt", a, e)) {
			e.preventDefault();
			return;
		}
		declined = a;
		setTimeout(() => {
			declined = null;
		}, 0);
	};

	root.addEventListener("click", onClick);
	root.addEventListener("keydown", onKeyDown);
	return () => {
		root.removeEventListener("click", onClick);
		root.removeEventListener("keydown", onKeyDown);
	};
}

/**
 * `catchAnchors` on the element `ref` holds, for as long as the component is
 * mounted. The rule is read at event time, so a new one each render is fine.
 */
export function useAnchorCatcher(
	ref: RefObject<HTMLElement | null>,
	rule: AnchorRule = defaultAnchorRule,
): void {
	const current = useRef(rule);
	current.current = rule;
	useEffect(() => {
		const el = ref.current;
		if (!el) return;
		return catchAnchors(el, (...args) => current.current(...args));
	}, [ref]);
}

/**
 * A box that routes the in-app links inside it. `display: contents`, so it
 * adds no layout of its own.
 */
export function AnchorCatcher({ rule, children }: { rule?: AnchorRule; children?: ReactNode }) {
	const ref = useRef<HTMLDivElement | null>(null);
	useAnchorCatcher(ref, rule ?? defaultAnchorRule);
	return (
		<div ref={ref} data-slot="anchor-catcher" className="contents">
			{children}
		</div>
	);
}
