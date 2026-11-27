// Change and submit: the two things an editable surface says.
//
// A change is bookkeeping: the value moved and this is it now. Text editors
// (the code editor, the markdown editor, the text area) send one at a quiet
// moment while you type and on blur, the way every app with autosave does,
// and an inline field sends one on blur. A change never runs anything on its
// own.
//
// A submit is intent: the person pressed the send key (Enter in a one-line
// field, shift+Enter in a multi-line one, or the swap with `submit_on`).
// Nothing else submits: not a blur, not a quiet moment, not Escape.
//
// Which one to listen to is the owner's call. A store that mirrors the text
// follows changes; a host that acts on the text (runs code, sends a message)
// follows submits, and its text is "unsaved" until one lands. Such a host can
// guard the page with `useLeaveGuard`, so a reload or a closed tab asks first.

import { useEffect } from "react";

/** The quiet moment a text editor waits before it sends a change. Long enough that a typist never triggers it. */
export const SAVE_DELAY = 800;

const guards = new Set<symbol>();

function onBeforeUnload(e: BeforeUnloadEvent): void {
	if (guards.size === 0) return;
	e.preventDefault();
	// Older browsers ask only when a return value is set.
	e.returnValue = "";
}

/**
 * While `active`, leaving the page (a reload, a closed tab) asks first, the
 * browser's own prompt. One listener for the page however many guards are
 * up; it asks while any of them is.
 */
export function useLeaveGuard(active: boolean): void {
	useEffect(() => {
		if (!active) return;
		const token = Symbol("leave-guard");
		if (guards.size === 0) window.addEventListener("beforeunload", onBeforeUnload);
		guards.add(token);
		return () => {
			guards.delete(token);
			if (guards.size === 0) window.removeEventListener("beforeunload", onBeforeUnload);
		};
	}, [active]);
}
