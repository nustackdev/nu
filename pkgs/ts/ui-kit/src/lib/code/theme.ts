// The code view's look, wired to the design tokens.
//
// CodeMirror themes are plain CSS, so every color here is a `var(--...)` and
// the `.dark` flip on <html> restyles every open view with no observer and no
// redefine step. Syntax colors are the eight `--syntax-*` roles in index.css;
// a tag that maps to none of them reads as body text, which is most of them.

import { HighlightStyle } from "@codemirror/language";
import { EditorView } from "@codemirror/view";
import { tags as t } from "@lezer/highlight";

export const kitTheme = EditorView.theme({
	"&": {
		color: "var(--text-primary)",
		backgroundColor: "transparent",
		fontSize: "var(--text-sm)",
	},
	"&.cm-focused": { outline: "none" },
	// The height bounds come from the host as custom properties, so a prop
	// change is a style change and never a reconfigure.
	".cm-scroller": {
		fontFamily: "var(--font-mono)",
		lineHeight: "1.5",
		minHeight: "var(--nu-code-min, 0)",
		maxHeight: "var(--nu-code-max, none)",
		overflow: "auto",
	},
	".cm-content": {
		padding: "12px 0",
		caretColor: "var(--accent)",
	},
	".cm-line": { padding: "0 12px" },
	".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--accent)" },
	"&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection":
		{ backgroundColor: "var(--accent-soft)" },
	".cm-gutters": {
		backgroundColor: "transparent",
		color: "var(--text-muted)",
		border: "none",
	},
	".cm-lineNumbers .cm-gutterElement": { padding: "0 4px 0 12px", minWidth: "28px" },
	".cm-activeLineGutter": { backgroundColor: "transparent", color: "var(--text-secondary)" },
	".cm-matchingBracket, &.cm-focused .cm-matchingBracket": {
		backgroundColor: "var(--accent-wash)",
		outline: "1px solid var(--accent-line)",
	},
	".cm-nonmatchingBracket": { backgroundColor: "var(--status-danger-wash)" },
	".cm-searchMatch": {
		backgroundColor: "var(--status-warn-wash)",
		outline: "1px solid var(--status-warn-line)",
	},
	".cm-searchMatch.cm-searchMatch-selected": {
		backgroundColor: "var(--accent-soft)",
		outline: "1px solid var(--accent-line)",
	},
	".cm-panels": {
		backgroundColor: "var(--bg-elevated)",
		color: "var(--text-primary)",
	},
	".cm-panels-bottom": { borderTop: "1px solid var(--border-default)" },
	".cm-tooltip": {
		backgroundColor: "var(--bg-elevated)",
		color: "var(--text-primary)",
		border: "1px solid var(--border-default)",
		borderRadius: "6px",
		overflow: "hidden",
	},
	".cm-tooltip.cm-tooltip-autocomplete > ul": {
		fontFamily: "var(--font-mono)",
		fontSize: "var(--text-sm)",
	},
	".cm-tooltip-autocomplete ul li[aria-selected]": {
		backgroundColor: "var(--accent-soft)",
		color: "var(--text-primary)",
	},
	".cm-completionDetail": { color: "var(--text-muted)" },
	".cm-completionMatchedText": { textDecoration: "none", color: "var(--accent)" },
});

export const kitHighlight = HighlightStyle.define([
	{
		tag: [
			t.keyword,
			t.controlKeyword,
			t.definitionKeyword,
			t.moduleKeyword,
			t.operatorKeyword,
			t.self,
		],
		color: "var(--syntax-keyword)",
	},
	{
		tag: [t.string, t.special(t.string), t.regexp, t.character, t.docString],
		color: "var(--syntax-string)",
	},
	{
		tag: [t.number, t.bool, t.null, t.atom, t.constant(t.variableName)],
		color: "var(--syntax-constant)",
	},
	{
		tag: [
			t.function(t.variableName),
			t.function(t.definition(t.variableName)),
			t.function(t.propertyName),
		],
		color: "var(--syntax-function)",
	},
	{
		tag: [t.className, t.typeName, t.definition(t.className), t.namespace],
		color: "var(--syntax-type)",
	},
	{ tag: [t.meta, t.annotation, t.processingInstruction], color: "var(--syntax-meta)" },
	{
		tag: [t.comment, t.lineComment, t.blockComment, t.docComment],
		color: "var(--syntax-comment)",
		fontStyle: "italic",
	},
	{ tag: [t.punctuation, t.operator, t.bracket, t.separator], color: "var(--syntax-punct)" },
	// markup: markdown and html sources read as documents, not as code
	{ tag: t.heading, color: "var(--syntax-keyword)", fontWeight: "600" },
	{ tag: t.strong, fontWeight: "600" },
	{ tag: t.emphasis, fontStyle: "italic" },
	{ tag: t.strikethrough, textDecoration: "line-through" },
	{ tag: [t.link, t.url], color: "var(--syntax-constant)", textDecoration: "underline" },
	{ tag: [t.tagName, t.angleBracket], color: "var(--syntax-keyword)" },
	{ tag: t.attributeName, color: "var(--syntax-type)" },
	{ tag: t.invalid, color: "var(--status-danger)" },
]);
