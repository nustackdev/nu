// Touch mode: the kit's one answer to "is this a phone".
//
// Touch mode is about the hand, not the screen. A device whose main pointer is
// coarse and cannot hover (a phone, a tablet without a trackpad) gets touch
// interactions: overlays as bottom sheets, long-press for the context menu, no
// hover reveals, no tooltips, bigger tap areas. Width is a separate question
// that each component answers from its own box (container queries), so a
// narrow desktop column gets the narrow layout with mouse interactions, and a
// tablet gets touch interactions with the wide layout.
//
// Read once, when the page loads, and never again: a page does not switch
// modes while it is open, a reload reads again. Never from the user agent:
// "request desktop site" fakes the UA, not the pointer, so a phone stays a
// phone. An iPad with a trackpad reports a fine pointer and gets desktop.
//
// Components read `useTouch()`, none of them queries the device on its own.
// The kit's touch CSS keys on `data-nu-touch` on the document element, set
// here at load when the device is touch. `TouchProvider` forces a mode for a
// subtree, and marks the document to match while it is mounted: for stories
// and tests, never for an app.

import { createContext, createElement, type ReactNode, useContext, useLayoutEffect } from "react";

/** The media query that makes a device touch: a coarse main pointer that cannot hover. */
export const TOUCH_QUERY = "(pointer: coarse) and (hover: none)";

/** The document attribute the kit's touch CSS keys on. */
export const TOUCH_ATTR = "data-nu-touch";

/** How long a finger rests before it is a long-press (the touch right-click), in ms. */
export const LONG_PRESS_MS = 500;
/** How far it may drift meanwhile, in px, before it is a scroll instead. */
export const LONG_PRESS_SLOP = 10;

function detect(): boolean {
	if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
	return window.matchMedia(TOUCH_QUERY).matches;
}

/** Whether this page load is on a touch device. Read once, at load. */
export const touchDevice: boolean = detect();

function mark(on: boolean): void {
	if (typeof document === "undefined") return;
	document.documentElement.toggleAttribute(TOUCH_ATTR, on);
}

mark(touchDevice);

const TouchContext = createContext<boolean>(touchDevice);

/** True in touch mode. Constant for the life of the page, outside a `TouchProvider`. */
export function useTouch(): boolean {
	return useContext(TouchContext);
}

/**
 * Force touch mode on or off for `children`, and mark the document to match
 * while mounted. For stories and tests: an app never sets the mode itself.
 */
export function TouchProvider({ value, children }: { value: boolean; children?: ReactNode }) {
	useLayoutEffect(() => {
		const before = document.documentElement.hasAttribute(TOUCH_ATTR);
		mark(value);
		return () => mark(before);
	}, [value]);
	return createElement(TouchContext.Provider, { value }, children);
}
