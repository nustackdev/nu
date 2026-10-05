// The code engine's extension sets, shared by every CodeMirror view in the kit.
//
// Two views run on this engine: `CodeMirrorView` (./view.tsx), which owns one
// string and saves it itself, and the markdown editor's code fences
// (lib/markdown/fence.tsx), which are windows onto text that ProseMirror owns.
// They must look and type the same, so the look and the editing behaviour live
// here once and each view adds only what is its own.
//
// The split is by who owns the text. `codeBase` is the look, the same for
// both. `codeEditing` is everything that only means something while the text
// can change, minus the parts that decide where an edit goes: undo history
// and the deliberate-save key. A view that owns its text asks for history and
// passes its save key; a fence asks for neither, because undo and saving
// belong to the document it sits in.

import {
	autocompletion,
	closeBrackets,
	closeBracketsKeymap,
	completionKeymap,
} from "@codemirror/autocomplete";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import {
	bracketMatching,
	indentOnInput,
	indentUnit,
	syntaxHighlighting,
} from "@codemirror/language";
import { highlightSelectionMatches, searchKeymap } from "@codemirror/search";
import { EditorState, type Extension, Prec } from "@codemirror/state";
import {
	drawSelection,
	EditorView,
	highlightActiveLineGutter,
	highlightSpecialChars,
	type KeyBinding,
	keymap,
	lineNumbers,
} from "@codemirror/view";
import { kitSearch } from "./search";
import { kitHighlight, kitTheme } from "./theme";

/** The look, and the few settings that decide how text is laid out. */
export const codeBase: Extension = [
	highlightSpecialChars(),
	drawSelection(),
	EditorState.tabSize.of(4),
	indentUnit.of("    "),
	syntaxHighlighting(kitHighlight),
	kitTheme,
];

/** Selectable and copyable, nothing more: no keymaps, no history, no completion. */
export const codeReading: Extension = [
	EditorView.editable.of(false),
	EditorState.readOnly.of(true),
];

export const codeGutter: Extension = [lineNumbers(), highlightActiveLineGutter()];

export type CodeEditingOptions = {
	/** CodeMirror's own undo stack. Off when the text belongs to a bigger document. */
	history?: boolean;
	/** Bindings that win over every default, for the host's own keys. */
	keys?: readonly KeyBinding[];
};

/** Everything that only means something while the text can change. */
export function codeEditing({
	history: undoable = false,
	keys = [],
}: CodeEditingOptions = {}): Extension {
	return [
		EditorView.editable.of(true),
		EditorState.readOnly.of(false),
		undoable ? history() : [],
		indentOnInput(),
		bracketMatching(),
		closeBrackets(),
		autocompletion(),
		highlightSelectionMatches(),
		kitSearch(),
		keys.length ? Prec.highest(keymap.of(keys)) : [],
		keymap.of([
			...closeBracketsKeymap,
			...defaultKeymap,
			...searchKeymap,
			...(undoable ? historyKeymap : []),
			...completionKeymap,
			indentWithTab,
		]),
	];
}
