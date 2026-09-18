// Monaco, assembled by hand.
//
// We do NOT import `monaco-editor` or `editor.main`: those pull the LSP client
// and ~90 language registrations we will never use. Instead we take
// `editor.api` (the surface) plus the handful of editor contributions that
// make a code box feel like an editor, plus a short list of grammars.
//
// Each grammar's `register.js` is tiny and only declares the language; the
// tokenizer behind it is a dynamic import inside that module, so it lands in
// its own chunk and loads the first time an editor is set to that language.
// A language id outside this list still works, it just renders unhighlighted.
//
// Monaco owns the contents of ONE editor and nothing else. It has no idea a
// node tree exists. That is the borrow boundary, and it is the same boundary
// the prose editor sits behind.

import * as monaco from "monaco-editor/editor/editor.api.js";

import { KIT_THEME } from "./loader";

import "monaco-editor/editor/contrib/bracketMatching/browser/bracketMatching.js";
import "monaco-editor/editor/contrib/clipboard/browser/clipboard.js";
import "monaco-editor/editor/contrib/comment/browser/comment.js";
import "monaco-editor/editor/contrib/cursorUndo/browser/cursorUndo.js";
import "monaco-editor/editor/contrib/find/browser/findController.js";
import "monaco-editor/editor/contrib/indentation/browser/indentation.js";
import "monaco-editor/editor/contrib/linesOperations/browser/linesOperations.js";
import "monaco-editor/editor/contrib/multicursor/browser/multicursor.js";
import "monaco-editor/editor/contrib/smartSelect/browser/smartSelect.js";
import "monaco-editor/editor/contrib/wordOperations/browser/wordOperations.js";

import "monaco-editor/languages/definitions/css/register.js";
import "monaco-editor/languages/definitions/html/register.js";
import "monaco-editor/languages/definitions/javascript/register.js";
import "monaco-editor/languages/definitions/markdown/register.js";
import "monaco-editor/languages/definitions/python/register.js";
import "monaco-editor/languages/definitions/shell/register.js";
import "monaco-editor/languages/definitions/sql/register.js";
import "monaco-editor/languages/definitions/typescript/register.js";
import "monaco-editor/languages/definitions/yaml/register.js";

import EditorWorker from "monaco-editor/editor/editor.worker.js?worker";

// No language services are registered, so the only worker anyone asks for is
// the base editor worker (diffing, links, basic word completions).
(self as unknown as { MonacoEnvironment: unknown }).MonacoEnvironment = {
	getWorker: () => new EditorWorker(),
};

// One theme, wired to the design tokens. Monaco cannot read CSS variables, so
// the kit resolves them here, at define time.
//
// Deliberately NOT two themes defined once: a token only resolves to the theme
// that is live on <html> at the moment it is read, so defining a light theme
// while the page is dark bakes dark hexes into the light theme. Instead one
// theme is redefined from whatever is live, every time the theme flips.

function cssVar(name: string, fallback: string): string {
	const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
	return v || fallback;
}

/** (Re)define the kit theme from the live design tokens and make it active. */
export function applyKitTheme(): void {
	const dark = document.documentElement.classList.contains("dark");

	const bg = cssVar("--bg-sunken", "#f7f7f8");
	const fg = cssVar("--text-primary", "#1a1a1a");
	const muted = cssVar("--text-muted", "#8a8a8a");
	const accent = cssVar("--accent", "#7c5cff");
	const accent2 = cssVar("--accent-2", "#3b82f6");
	const line = cssVar("--border-subtle", "#e5e5e5");

	const rules = [
		{ token: "comment", foreground: muted, fontStyle: "italic" },
		{ token: "string", foreground: accent2 },
		{ token: "keyword", foreground: accent },
		{ token: "number", foreground: accent2 },
	].map((r) => ({ ...r, foreground: r.foreground.replace("#", "") }));

	const colors = (base: string) => ({
		"editor.background": base,
		"editor.foreground": fg,
		"editorLineNumber.foreground": muted,
		"editorLineNumber.activeForeground": fg,
		"editorIndentGuide.background1": line,
		"editorIndentGuide.activeBackground1": line,
		"editor.lineHighlightBorder": "#00000000",
		"editorCursor.foreground": accent,
	});

	monaco.editor.defineTheme(KIT_THEME, {
		base: dark ? "vs-dark" : "vs",
		inherit: true,
		rules,
		colors: colors(bg),
	});
	monaco.editor.setTheme(KIT_THEME);
}

export { monaco };
