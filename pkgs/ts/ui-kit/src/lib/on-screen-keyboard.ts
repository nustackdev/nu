// The on-screen keyboard: how much of the page it covers.
//
// A phone's keyboard does not shrink the layout viewport, the one `fixed`
// elements sit in: it shrinks the visual viewport over it. What it covers is
// the layout viewport's height less the visual viewport's bottom edge (its
// height plus how far it is scrolled down), the browser's own pan included.
//
// While pinch-zoomed the visual viewport is smaller for another reason, so a
// zoomed page reads as no keyboard. A difference under `KEYBOARD_MIN_PX` is a
// browser bar settling, not a keyboard.
//
// The bottom sheet (../components/ui/bottom-sheet.tsx) rides on this: lifted
// by the inset while the keyboard is up, never stretched.

import { useEffect, useState } from "react";

/** Below this the visual viewport moved for the browser's bars, not a keyboard. */
export const KEYBOARD_MIN_PX = 60;

/** The visual viewport fields the inset reads. */
export type ViewportBox = { height: number; offsetTop: number; scale: number };

/** How many px of the layout viewport's bottom the keyboard covers; 0 for none. */
export function keyboardInset(layoutHeight: number, viewport: ViewportBox | null): number {
	if (!viewport || Math.abs(viewport.scale - 1) > 0.01) return 0;
	const covered = Math.round(layoutHeight - viewport.height - viewport.offsetTop);
	return covered >= KEYBOARD_MIN_PX ? covered : 0;
}

/** The keyboard: its inset and the height left visible above it, live while `enabled`. */
export function useOnScreenKeyboard(enabled = true): { inset: number; visible: number } {
	const [state, setState] = useState({ inset: 0, visible: 0 });
	useEffect(() => {
		const vv = typeof window === "undefined" ? null : window.visualViewport;
		if (!enabled || !vv) return;
		const read = () => {
			const inset = keyboardInset(window.innerHeight, vv);
			const visible = inset ? Math.round(vv.height) : 0;
			setState((was) =>
				was.inset === inset && was.visible === visible ? was : { inset, visible },
			);
		};
		read();
		vv.addEventListener("resize", read);
		vv.addEventListener("scroll", read);
		return () => {
			vv.removeEventListener("resize", read);
			vv.removeEventListener("scroll", read);
		};
	}, [enabled]);
	return state;
}
