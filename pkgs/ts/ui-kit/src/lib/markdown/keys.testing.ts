// The platform's real keys, for the browser tests.
//
// ProseMirror's `Mod` is Cmd on a Mac and Ctrl elsewhere, decided the way
// prosemirror-keymap decides it. A test that presses the other platform's
// key tests nothing, so the browser tests take theirs from here.

/** Whether the browser runs on a Mac, as prosemirror-keymap tells. */
export const MAC =
	typeof navigator !== "undefined" && /Mac|iP(hone|[oa]d)/.test(navigator.platform);

/** Mod-Enter: Cmd on a Mac, Ctrl elsewhere. */
export const MOD_ENTER = MAC ? "{Meta>}{Enter}{/Meta}" : "{Control>}{Enter}{/Control}";
