// Lazy gate in front of Monaco.
//
// Monaco is ~4MB and most pages never open a code editor, so it lives behind a
// dynamic import and lands in its own chunk. The first editor that mounts pays
// for it; every other node in the kit paints immediately.
//
// Types come from a type-only import, which the compiler erases, so nothing
// here pulls Monaco into the initial graph. That is the whole reason this file
// and ./impl.ts are two files: anything that touches the real module has to
// stay on the far side of the dynamic import.

import type * as MonacoNS from "monaco-editor/editor/editor.api.js";

export type { MonacoNS };

/**
 * The single Monaco theme name. One theme, redefined from the live tokens on
 * every flip, rather than two defined once - see `./impl.applyKitTheme`.
 */
export const KIT_THEME = "nu";
export type MonacoApi = typeof MonacoNS;
export type CodeEditor = MonacoNS.editor.IStandaloneCodeEditor;
export type KeyboardEvt = MonacoNS.IKeyboardEvent;

let pending: Promise<MonacoApi> | null = null;
let impl: typeof import("./impl") | null = null;
let watching = false;

/** Load Monaco (once), stained with the live design tokens. */
export function loadMonaco(): Promise<MonacoApi> {
	if (!pending) {
		pending = import("./impl").then((m) => {
			impl = m;
			m.applyKitTheme();
			watchTheme();
			return m.monaco;
		});
	}
	return pending;
}

// The kit's theme is the `.dark` class on <html>, and whoever owns the
// preference flips it. Monaco cannot read CSS variables, so it has to be told.
// One observer for the whole app rather than one per editor, and it starts on
// first load rather than at import time, so a page with no editor open never
// drags Monaco into the execution path to restain nothing.
function watchTheme(): void {
	if (watching || typeof MutationObserver === "undefined") return;
	watching = true;
	const observer = new MutationObserver(() => {
		impl?.applyKitTheme();
	});
	observer.observe(document.documentElement, {
		attributes: true,
		attributeFilter: ["class"],
	});
}
