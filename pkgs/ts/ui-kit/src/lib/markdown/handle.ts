// The markdown handle: what one markdown editor tells the host that owns a
// sequence of them, and what that host tells it back.
//
// The editor owns exactly one markdown value and knows nothing about its
// neighbours (see ./editor.tsx, "what is deliberately not here"). A host that
// lays editors out in a sequence, a page of cells, a notebook, does know
// them, and wants writing to flow across the seams: the caret arrowing out of
// the last line into the next editor, Backspace on a blank one removing
// it, Cmd-Enter opening a new one below. None of that can be decided here,
// and none of it should be decided above by reading this editor's DOM. So the
// editor reports intents and takes commands.
//
// ## Intents out
//
// ProseMirror runs every plugin's key handler in order and falls back to the
// browser only when all of them decline. The intents plugin goes last, so it
// sees exactly the keys the document had no use for: an arrow the lists,
// tables, fences and gap cursor all let through, a Backspace nothing could
// join, a Cmd-Enter outside a table. It reports those to the host as a
// `MarkdownIntent`. The host answers true when it acted (the key is consumed) and
// false to let the editor go on as if no host existed. With no host listening
// the plugin does nothing at all.
//
// `leave` is the document's own idea of its edge, not a guess from
// coordinates: the caret sits in the first (last) textblock of the document
// with nothing before (after) it at any level, and `view.endOfTextblock`
// says it is on that block's first (last) visual line. So a wrapped
// paragraph, a list's last item, a table's last row (through the gap cursor
// first) and a quote all behave alike, and the host never learns any of them.
//
// ## Commands in
//
// A `MarkdownHandle` is the whole of what a host can do to an editor:
// focus it (at an edge, under an x, or where its caret already is), ask
// whether it is blank, read its markdown, cut it at the caret, append
// markdown at its end, type as if at the keyboard, save now. Every command
// goes through the editor's own transactions and its own focus, so there is
// nothing for a DOM selection restore to race with.
//
// The handle is additive: an editor with no `onHandle` host runs exactly
// as before.

import { GapCursor } from "prosemirror-gapcursor";
import { keydownHandler } from "prosemirror-keymap";
import type { Node as PMNode, ResolvedPos } from "prosemirror-model";
import { type Command, NodeSelection, Plugin, Selection, TextSelection } from "prosemirror-state";
import { isInTable } from "prosemirror-tables";
import type { EditorView } from "prosemirror-view";
import type { Markdown } from "./markdown";
import { isBlank } from "./rules";
import type { ProseSchema } from "./schema";

/** The side of the document the caret tried to cross. */
export type LeaveDir = "up" | "down" | "left" | "right";

/** What the person tried to do that the document could not do alone. */
export type MarkdownIntent =
	/**
	 * The caret (the selection's head, with `extend`, for Shift+arrow) tried
	 * to cross the document's edge. `x` is the caret's horizontal position on
	 * screen, so the next editor can land under it.
	 */
	| { kind: "leave"; dir: LeaveDir; extend: boolean; x: number }
	/**
	 * Backspace at the very start, or Delete at the very end, of a top-level
	 * textblock or a gap cursor at the edge, that the editor had no use for.
	 * Never from inside a table cell.
	 */
	| { kind: "erase"; dir: "back" | "forward" }
	/** "/" typed into a blank document, reported before it lands. */
	| { kind: "slash" }
	/**
	 * Mod-Enter outside a table or fence. `at` is "end" when nothing but empty
	 * textblocks follow the caret, "mid" otherwise. A selection is deleted
	 * first, the way Enter would, and `at` decided for the caret that leaves.
	 */
	| { kind: "break"; at: "end" | "mid" };

/**
 * Where `focus` puts the caret. "kept" focuses without moving the editor's
 * own selection, which it keeps while blurred. `{x, edge}` lands on the
 * first (last) line under the screen x: in a table, the cell under x in its
 * first (last) row; in a fence, its first (last) line nearest x; past a
 * line's end, the line's end.
 */
export type FocusAt = "start" | "end" | "kept" | { x: number; edge: "first" | "last" };

/** A host's answer to an intent: true when it acted. */
export type IntentListener = (intent: MarkdownIntent) => boolean;

export interface MarkdownHandle {
	/** Sets the editor's own selection, then focuses it. */
	focus(at: FocusAt): void;
	/** One empty paragraph and nothing else: the same check the placeholder uses. */
	blank(): boolean;
	/** The current markdown, unsaved edits included. */
	markdown(): string;
	/** The markdown after the caret, read only. What `split` would return. */
	tail(): string;
	/** Cuts the document at the caret: keeps the head, returns the tail as markdown. */
	split(): string;
	/**
	 * `split` with its save held, for a host moving the tail into another
	 * document. The cut shows at once, but this document saves nothing (no
	 * autosave, no save on blur, `commit` waits) until the host says how the
	 * move ended: `keep`, and the cut goes out with any edits since; `undo`,
	 * and the tail comes back, then saves resume. Until then the store still
	 * has the tail here, so it is never in neither document.
	 */
	cut(): Cut;
	/** Adds blocks at the end, caret at the join. Into a blank document, replaces its empty paragraph. */
	append(md: string): void;
	/** Text at the caret as if typed, input rules included. "\n" is Enter. */
	type(text: string): void;
	/** Saves now instead of at the next quiet moment. */
	commit(): void;
	/**
	 * Calls `fn` once the current text is in the store: at once when nothing
	 * is unsaved or waiting to be read back, otherwise when the read for the
	 * latest save is answered (unsaved edits are saved first, at the next
	 * commit). Returns the unsubscribe. An editor with no store behind it
	 * (a plain editor, no node) counts a commit as the store. `lost`, when
	 * the editor or its node goes away first: that text will never be stored.
	 */
	saved(fn: () => void, lost?: () => void): () => void;
	/**
	 * A hint the editor draws for the host, the way it draws its placeholder
	 * (a decoration, never document content). "blank", the default: on a
	 * blank document, in place of the editor's own placeholder while set.
	 * "tail": on an empty last line of a document that has text, the line
	 * Enter leaves you on. Null clears it. Never drawn read-only.
	 */
	hint(text: string | null, at?: "blank" | "tail"): void;
	/** Hear the editor's intents. Returns the unsubscribe. The first listener to answer true wins. */
	onIntent(fn: IntentListener): () => void;
}

/** A held cut (`MarkdownHandle.cut`): the tail it took, and how the move ended. */
export type Cut = {
	tail: string;
	/** The tail is safe elsewhere: the cut is saved, with any edits since. */
	keep(): void;
	/** It is not: the tail comes back, then saves resume. */
	undo(): void;
};

/** What the editor hands the contract: its codec, its commands, its fences. */
export type HandleSeams = {
	schema: ProseSchema;
	md: Markdown;
	/** Save now. */
	commit: () => void;
	/** `MarkdownHandle.saved`; the editor composes it from its own dirty state and the owner's store. */
	saved: (fn: () => void, lost?: () => void) => () => void;
	/** Hold the editor's saves until the returned release, when what is unsaved goes out. */
	hold: () => () => void;
	/** What the editor binds Enter to, so `type("\n")` is the same key. */
	enter: Command;
	/**
	 * The document position on the fence at `pos` nearest screen x on its
	 * first or last line, or null when there is no laid-out fence there.
	 */
	fenceAtX: (pos: number, x: number, edge: "first" | "last") => number | null;
};

export type HandleContract = {
	/** The intents plugin. Goes last in the editor's plugin list. */
	plugin: Plugin;
	/** Offer an intent to the listeners. True when one acted. */
	report: (intent: MarkdownIntent) => boolean;
	/** The handle over the live view. */
	handle: (view: EditorView) => MarkdownHandle;
	/** What the host asked drawn (see `MarkdownHandle.hint`); the editor's decorations read these. */
	hints: { blank: () => string | null; tail: () => string | null };
};

/** Marks a transaction that only changes what the editor draws, not the document. */
const HINT = "nu-hint";

/* ============================== edges ==================================== */

function back(dir: LeaveDir): boolean {
	return dir === "up" || dir === "left";
}

/**
 * The position that would cross the edge, or null when this selection is
 * not one that leaves: a text selection without Shift collapses first
 * (the browser's own move), and a table's cell selection stays a table's.
 */
function edgeHead(sel: Selection, dir: LeaveDir, extend: boolean): ResolvedPos | null {
	if (sel instanceof TextSelection) return extend || sel.empty ? sel.$head : null;
	if (sel instanceof GapCursor) return sel.$head;
	if (sel instanceof NodeSelection) return back(dir) ? sel.$from : sel.$to;
	return null;
}

/**
 * Nothing the caret could still reach that way: first (last) child at every
 * level above, and at the edge of its own block. In a textblock, up and
 * down ask the view, since only layout knows which visual line the caret is
 * on; left and right are the block's own offsets. Up and down do not care
 * which cell of a table row the caret is in: the row is the vertical unit.
 */
function atEdge(view: EditorView, $p: ResolvedPos, dir: LeaveDir): boolean {
	const first = back(dir);
	const vertical = dir === "up" || dir === "down";
	for (let d = 0; d < $p.depth; d++) {
		if (vertical && $p.node(d).type.spec.tableRole === "row") continue;
		if (first ? $p.index(d) !== 0 : $p.index(d) !== $p.node(d).childCount - 1) return false;
	}
	if ($p.parent.isTextblock) {
		if (dir === "left") return $p.parentOffset === 0;
		if (dir === "right") return $p.parentOffset === $p.parent.content.size;
		return view.endOfTextblock(dir);
	}
	return first ? $p.parentOffset === 0 : $p.parentOffset === $p.parent.content.size;
}

/** Only empty textblocks follow `pos`: the caret is at the end, for `break`. */
function nothingAfter(doc: PMNode, pos: number): boolean {
	let empty = true;
	doc.cut(pos).descendants((node) => {
		if (!empty) return false;
		if (node.isTextblock) {
			if (node.content.size > 0) empty = false;
			return false;
		}
		if (node.isLeaf || node.type.spec.tableRole) {
			empty = false;
			return false;
		}
		return true;
	});
	return empty;
}

/**
 * Where a cut at the caret starts. Mid-text it is the caret itself. At the
 * start of a block it is the block's boundary, and the boundary of every
 * ancestor it starts, so a cut at the first item of a list takes the whole
 * list and a cut at the start of the document takes everything. At the end
 * of a block it is the boundary after it, and after every ancestor it ends,
 * so a cut at the end of an item leaves that item whole above and takes no
 * empty remainder of it (an empty `- `, `#` or `>`) into the tail.
 */
function cutPoint($head: ResolvedPos): number {
	if ($head.parentOffset === 0) {
		let d = $head.depth;
		while (d > 1 && $head.index(d - 1) === 0) d--;
		return $head.before(d);
	}
	if ($head.parentOffset === $head.parent.content.size) {
		let d = $head.depth;
		while (d > 1 && $head.index(d - 1) === $head.node(d - 1).childCount - 1) d--;
		return $head.after(d);
	}
	return $head.pos;
}

/** The first (last) textblock's content range inside `block`, which starts at `pos`. */
function edgeTextblock(
	block: PMNode,
	pos: number,
	edge: "first" | "last",
): { start: number; end: number } | null {
	if (block.isTextblock) return { start: pos + 1, end: pos + 1 + block.content.size };
	let found: { start: number; end: number } | null = null;
	block.descendants((node, offset) => {
		if (!node.isTextblock) return true;
		const start = pos + 1 + offset + 1;
		const range = { start, end: start + node.content.size };
		if (edge === "last" || !found) found = range;
		return false;
	});
	return found;
}

/* ============================== the contract ============================= */

/**
 * The contract for one editor. Build one per view: the plugin reports to
 * the listeners the handle collects.
 */
export function createHandle(seams: HandleSeams): HandleContract {
	const { schema: s, md } = seams;
	const listeners = new Set<IntentListener>();
	const hints: { blank: string | null; tail: string | null } = { blank: null, tail: null };

	const report = (intent: MarkdownIntent): boolean => {
		for (const fn of listeners) if (fn(intent)) return true;
		return false;
	};

	const leave =
		(dir: LeaveDir, extend: boolean): Command =>
		(state, _dispatch, view) => {
			const $head = edgeHead(state.selection, dir, extend);
			if (!$head || !view || !atEdge(view, $head, dir)) return false;
			return report({ kind: "leave", dir, extend, x: view.coordsAtPos($head.pos).left });
		};

	const erase =
		(dir: "back" | "forward"): Command =>
		(state) => {
			const sel = state.selection;
			const start = dir === "back";
			if (sel instanceof GapCursor) {
				if (sel.head !== (start ? 0 : state.doc.content.size)) return false;
				return report({ kind: "erase", dir });
			}
			if (!(sel instanceof TextSelection) || !sel.empty) return false;
			const $h = sel.$head;
			if ($h.depth !== 1) return false;
			const atEnd =
				$h.parentOffset === $h.parent.content.size && $h.index(0) === state.doc.childCount - 1;
			if (start ? $h.parentOffset !== 0 || $h.index(0) !== 0 : !atEnd) return false;
			return report({ kind: "erase", dir });
		};

	const breakOut: Command = (state, dispatch, view) => {
		if (isInTable(state) || state.selection.$head.parent.type.spec.code) return false;
		if (!state.selection.empty) dispatch?.(state.tr.deleteSelection().scrollIntoView());
		const now = view ? view.state : state;
		const at = nothingAfter(now.doc, now.selection.$head.pos) ? "end" : "mid";
		return report({ kind: "break", at });
	};

	const keys = keydownHandler({
		ArrowUp: leave("up", false),
		ArrowDown: leave("down", false),
		ArrowLeft: leave("left", false),
		ArrowRight: leave("right", false),
		"Shift-ArrowUp": leave("up", true),
		"Shift-ArrowDown": leave("down", true),
		"Shift-ArrowLeft": leave("left", true),
		"Shift-ArrowRight": leave("right", true),
		Backspace: erase("back"),
		Delete: erase("forward"),
		"Mod-Enter": breakOut,
	});

	const plugin = new Plugin({
		props: {
			handleKeyDown(view, event) {
				if (listeners.size === 0) return false;
				// Before it lands: a keydown precedes the character. Shift is allowed,
				// since "/" needs it on some layouts.
				if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey) {
					return isBlank(view.state, s) && report({ kind: "slash" });
				}
				return keys(view, event);
			},
		},
	});

	/** The caret under screen x on the first (last) line, or null when layout cannot say. */
	const atX = (view: EditorView, x: number, edge: "first" | "last"): Selection | null => {
		const { doc } = view.state;
		const block = edge === "first" ? doc.firstChild : doc.lastChild;
		if (!block) return null;
		const pos = edge === "first" ? 0 : doc.content.size - block.nodeSize;
		if (block.type === s.nodeType.codeBlock) {
			const inside = seams.fenceAtX(pos, x, edge);
			return inside === null ? null : TextSelection.create(doc, inside);
		}
		const text = edgeTextblock(block, pos, edge);
		if (!text) return null;
		const line = view.coordsAtPos(edge === "first" ? text.start : text.end);
		// A caret box with no height is a document nobody has laid out.
		if (line.bottom <= line.top) return null;
		const box = view.dom.getBoundingClientRect();
		const left = Math.min(Math.max(x, box.left + 1), box.right - 1);
		const hit = view.posAtCoords({ left, top: (line.top + line.bottom) / 2 });
		if (!hit || hit.pos < pos || hit.pos > pos + block.nodeSize) return null;
		const $hit = doc.resolve(hit.pos);
		return $hit.parent.isTextblock ? TextSelection.create(doc, hit.pos) : null;
	};

	const selectionFor = (view: EditorView, at: Exclude<FocusAt, "kept">): Selection => {
		const { doc } = view.state;
		if (at === "start") return Selection.atStart(doc);
		if (at === "end") return Selection.atEnd(doc);
		return (
			atX(view, at.x, at.edge) ??
			(at.edge === "first" ? Selection.atStart(doc) : Selection.atEnd(doc))
		);
	};

	const handle = (view: EditorView): MarkdownHandle => {
		const h: MarkdownHandle = {
			focus(at) {
				if (at !== "kept") {
					const sel = selectionFor(view, at);
					if (!sel.eq(view.state.selection)) {
						view.dispatch(view.state.tr.setSelection(sel).scrollIntoView());
					}
				}
				view.focus();
			},

			blank: () => isBlank(view.state, s),

			markdown: () => md.serializeMarkdown(view.state.doc),

			tail() {
				const { doc, selection } = view.state;
				return md.serializeRange(doc, cutPoint(selection.$head), doc.content.size);
			},

			split() {
				const { state } = view;
				const from = cutPoint(state.selection.$head);
				const end = state.doc.content.size;
				const tail = md.serializeRange(state.doc, from, end);
				if (view.editable && from < end) {
					const tr = state.tr.delete(from, end);
					view.dispatch(tr.setSelection(Selection.atEnd(tr.doc)).scrollIntoView());
				}
				return tail;
			},

			cut() {
				const { state } = view;
				const from = cutPoint(state.selection.$head);
				const end = state.doc.content.size;
				const tail = md.serializeRange(state.doc, from, end);
				if (!view.editable || from >= end) return { tail, keep() {}, undo() {} };
				const release = seams.hold();
				const whole = state.doc;
				const tr = state.tr.delete(from, end);
				const head = tr.doc;
				view.dispatch(tr.setSelection(Selection.atEnd(tr.doc)).scrollIntoView());
				let open = true;
				return {
					tail,
					keep() {
						if (!open) return;
						open = false;
						release();
					},
					undo() {
						if (!open) return;
						open = false;
						// Torn down meanwhile: nothing here to put back, nor to save.
						if (view.isDestroyed) return;
						// Untouched since the cut, it goes back exactly as it was. Written
						// to since, the tail goes on the end, joined at a paragraph break:
						// not where it was, but kept.
						if (view.state.doc.eq(head)) {
							view.dispatch(view.state.tr.replaceWith(0, head.content.size, whole.content));
						} else {
							h.append(tail);
						}
						release();
					},
				};
			},

			append(text) {
				if (!view.editable) return;
				const { state } = view;
				const parsed = md.parseMarkdown(text).doc;
				const blankIn =
					parsed.childCount === 1 && parsed.firstChild?.type === s.nodeType.paragraph
						? parsed.firstChild.content.size === 0
						: false;
				if (blankIn) return;
				if (isBlank(state, s)) {
					const tr = state.tr.replaceWith(0, state.doc.content.size, parsed.content);
					view.dispatch(tr.setSelection(Selection.atStart(tr.doc)).scrollIntoView());
					return;
				}
				const at = state.doc.content.size;
				const tr = state.tr.insert(at, parsed.content);
				view.dispatch(tr.setSelection(Selection.near(tr.doc.resolve(at), 1)).scrollIntoView());
			},

			type(text) {
				if (!view.editable) return;
				for (const ch of text) {
					if (ch === "\n") {
						seams.enter(view.state, view.dispatch, view);
						continue;
					}
					// The view's own text input path: the input rules get the character
					// first, as they do for a keypress, and the plain insert is the
					// fallback they decline into.
					const { from, to } = view.state.selection;
					const insert = () => view.state.tr.insertText(ch, from, to).scrollIntoView();
					if (!view.someProp("handleTextInput", (f) => f(view, from, to, ch, insert))) {
						view.dispatch(insert());
					}
				}
			},

			commit: seams.commit,

			saved: seams.saved,

			hint(text, at = "blank") {
				if (hints[at] === text) return;
				hints[at] = text;
				// Nothing in the document changed; the decorations are read again.
				view.dispatch(view.state.tr.setMeta(HINT, true));
			},

			onIntent(fn) {
				listeners.add(fn);
				return () => {
					listeners.delete(fn);
				};
			},
		};
		return h;
	};

	return {
		plugin,
		report,
		handle,
		hints: { blank: () => hints.blank, tail: () => hints.tail },
	};
}
