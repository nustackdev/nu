// The code view: the engine behind the `Code` primitive's block mode.
//
// A CodeMirror view over exactly one string, the same deal the markdown
// editor strikes with one markdown document. It is both faces of a code surface:
// read-only it is a highlighted block you can select and copy from, editable
// it is an editor. One engine for both, so flipping between them changes
// nothing about how the code looks.
//
// Read-only is cheap on purpose. CodeMirror renders only what is on screen
// and a view with editing off carries no keymaps, no history and no
// completion, so a page of twenty code samples is twenty light views, not
// twenty editors.
//
// ## Saving
//
// Change and submit are two things (../save.ts). A commit (`onCommit`) is the
// change: it goes out at a quiet moment while you type and on blur, the way
// any editor autosaves, and one that round-trips to the same text is dropped.
// It runs nothing. The send key is the submit (`onSubmit`, with the text):
// it commits first, then submits. Shift+Enter with Enter the newline, or the
// other way round with `submitOn="enter"`. Nothing else submits. Cmd/ctrl+Enter
// does nothing here; it passes through to the app. Whatever the owner does
// with `value` in that submit (puts the declared text back, say) lands in the
// document. An owner that acts only on submits ignores the commits and keeps
// `value` at the last submit, so `onDirty`, the live read in between, says
// "not yet submitted".
//
// ## Diff
//
// Given an `original`, the view shows `value` as a unified diff against it
// (@codemirror/merge): removed lines as blocks above the lines that replaced
// them, added lines washed, runs of unchanged lines folded behind a bar you
// click to open. Highlighting stays on both sides. A diff is always read-only
// and carries no accept or reject buttons: it shows a change, it does not
// merge one.
//
// The merge extension sits in its own compartment like every other setting,
// but it fills that compartment twice when either text moves: empty, then
// fresh. Its fields only initialise when they join the state, so a single
// reconfigure would keep the old original, and the folds are worked out once,
// from the first diff. Emptying first makes the next diff a clean one.
//
// ## What is deliberately not here
//
// Nothing about neighbours. No arrow-out into a next block, no escape-to-
// parent, no focus protocol. Those only mean something to a host that owns a
// sequence of these, and this view owns exactly one value. `onView` hands the
// live view up so such a host can bind its own keys on top.
//
// Engine only: no box, no chrome. `Code` (components/ui/code.tsx) draws the
// surface around it. The extension sets themselves live in ./extensions.ts,
// shared with the markdown editor's code fences.

import { insertNewlineAndIndent } from "@codemirror/commands";
import { unifiedMergeView } from "@codemirror/merge";
import {
	Annotation,
	Compartment,
	EditorState,
	type Extension,
	Transaction,
} from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import type * as React from "react";
import { useCallback, useEffect, useLayoutEffect, useReducer, useRef } from "react";
import type { SubmitOn } from "../keyboard";
import { SAVE_DELAY } from "../save";
import { codeBase, codeEditing, codeGutter, codeReading } from "./extensions";
import { loadLanguage } from "./languages";
import { kitDiffTheme } from "./theme";

export type CodeMirrorViewProps = {
	/** The source. Owned by whoever renders this. */
	value: string;
	/** A language name or alias (`python`, `ts`, `sql`, `shell`). Unknown renders plain. */
	language?: string;
	/**
	 * The text `value` is compared against. Set, the view is a unified diff
	 * of the two, and read-only whatever `readOnly` says. `""` is a diff
	 * against nothing (every line added); unset is no diff.
	 */
	original?: string;
	/** On by default: a code view reads unless told it may be edited. */
	readOnly?: boolean;
	/** Defaults to on while editable, off while read-only. */
	lineNumbers?: boolean;
	/** Soft-wrap long lines instead of scrolling sideways. */
	wrap?: boolean;
	/** Height bounds in px. The view grows with its content between them; 0 is no bound. */
	minHeight?: number;
	maxHeight?: number;
	/** The change: a quiet moment, blur, and the send key, only when the text changed. Runs nothing. */
	onCommit?: (source: string) => void;
	/** The submit: the send key and nothing else, after its commit, with the text. */
	onSubmit?: (source: string) => void;
	/** Which key sends: shift+Enter (the default, Enter is the newline) or Enter. */
	submitOn?: SubmitOn;
	/** Whether the buffer differs from `value`, on every keystroke. */
	onDirty?: (dirty: boolean) => void;
	/**
	 * Every edit, keystroke by keystroke. `read` gives the buffer's text; call
	 * it only when the text is wanted, it walks the whole document.
	 */
	onEdit?: (read: () => string) => void;
	className?: string;
	/**
	 * Handed the live view on mount and null on teardown. The escape hatch for
	 * a host that needs to bind keys or drive the caret from above.
	 */
	onView?: (view: EditorView | null) => void;
};

/** Marks a transaction as the inbound value landing, not a keystroke. */
const inbound = Annotation.define<boolean>();

/**
 * The editing set, with this view's own undo stack and its send key. `mode`
 * is read on each press, so a `submitOn` change needs no rebuild: the send
 * key commits then submits, the other one is the newline.
 */
function editing(commit: () => void, submit: () => void, mode: () => SubmitOn): Extension {
	const send = () => {
		commit();
		submit();
		return true;
	};
	return codeEditing({
		history: true,
		keys: [
			{ key: "Enter", run: () => (mode() === "enter" ? send() : false) },
			{
				key: "Shift-Enter",
				run: (view) => (mode() === "enter" ? insertNewlineAndIndent(view) : send()),
			},
		],
	});
}

/** The unified diff of the doc against `original`: folded, no chunk buttons. */
function diffAgainst(original: string): Extension {
	return [
		unifiedMergeView({
			original,
			mergeControls: false,
			collapseUnchanged: { margin: 3, minSize: 4 },
		}),
		kitDiffTheme,
	];
}

export function CodeMirrorView({
	value,
	language = "",
	original,
	readOnly: readOnlyProp = true,
	lineNumbers: numbered,
	wrap = false,
	minHeight = 0,
	maxHeight = 0,
	onCommit,
	onSubmit,
	submitOn = "shift+enter",
	onDirty,
	onEdit,
	className,
	onView,
}: CodeMirrorViewProps) {
	const hostRef = useRef<HTMLDivElement | null>(null);
	const viewRef = useRef<EditorView | null>(null);
	/** The buffer changed since the last commit or inbound value. Gates inbound writes. */
	const dirtyRef = useRef(false);
	/** The diff compartment holds a merge view. */
	const armedRef = useRef(false);
	/** The quiet-moment commit, pending while you type. */
	const saveTimer = useRef<number | null>(null);
	// The view binds its listeners once, so everything they read goes through
	// a ref rather than a closed-over prop.
	const cb = useRef({ value, original, onCommit, onSubmit, submitOn, onDirty, onEdit, onView });
	cb.current = { value, original, onCommit, onSubmit, submitOn, onDirty, onEdit, onView };

	const diffing = original != null;
	const readOnly = readOnlyProp || diffing;
	const showNumbers = numbered ?? !readOnly;

	const slots = useRef({
		mode: new Compartment(),
		language: new Compartment(),
		gutter: new Compartment(),
		wrap: new Compartment(),
		diff: new Compartment(),
	}).current;

	const commit = useCallback(() => {
		if (saveTimer.current !== null) {
			window.clearTimeout(saveTimer.current);
			saveTimer.current = null;
		}
		const view = viewRef.current;
		if (!view) return;
		dirtyRef.current = false;
		const next = view.state.doc.toString();
		if (next === cb.current.value) return;
		cb.current.onCommit?.(next);
	}, []);

	// A submit can put the value back (`clear_on_submit`) in the same tick
	// that its commit moved it, and the two land as one render where `value`
	// never changed, so the inbound effect below would not run and the typed
	// text would stay. The bump makes it look again once that render is in.
	const [submits, bump] = useReducer((n: number) => n + 1, 0);
	const submit = useCallback(() => {
		cb.current.onSubmit?.(viewRef.current?.state.doc.toString() ?? cb.current.value);
		bump();
	}, []);

	const queueSave = useCallback(() => {
		if (saveTimer.current !== null) window.clearTimeout(saveTimer.current);
		saveTimer.current = window.setTimeout(() => {
			saveTimer.current = null;
			commit();
		}, SAVE_DELAY);
	}, [commit]);

	const modeFor = useCallback(
		(ro: boolean) => (ro ? codeReading : editing(commit, submit, () => cb.current.submitOn)),
		[commit, submit],
	);

	useLayoutEffect(() => {
		const host = hostRef.current;
		if (!host) return;

		const view = new EditorView({
			parent: host,
			state: EditorState.create({
				doc: cb.current.value,
				extensions: [
					slots.mode.of(modeFor(readOnly)),
					slots.language.of([]),
					slots.gutter.of(showNumbers ? codeGutter : []),
					slots.wrap.of(wrap ? EditorView.lineWrapping : []),
					slots.diff.of([]),
					codeBase,
					EditorView.updateListener.of((u) => {
						if (u.docChanged && u.transactions.some((tr) => !tr.annotation(inbound))) {
							dirtyRef.current = true;
							cb.current.onDirty?.(u.state.doc.toString() !== cb.current.value);
							cb.current.onEdit?.(() => u.state.doc.toString());
							queueSave();
						}
						if (u.focusChanged && !u.view.hasFocus) commit();
					}),
				],
			}),
		});
		viewRef.current = view;
		cb.current.onView?.(view);

		return () => {
			cb.current.onView?.(null);
			if (saveTimer.current !== null) window.clearTimeout(saveTimer.current);
			saveTimer.current = null;
			viewRef.current = null;
			view.destroy();
		};
		// The view is built once and driven imperatively from here on; every
		// prop below has its own effect that reconfigures one compartment.
	}, []);

	// -- inbound value -----------------------------------------------------
	//
	// Last actor wins, but not mid-keystroke: an inbound value never yanks text
	// out from under someone with uncommitted edits. Once the buffer is clean
	// the server's copy is the truth and gets adopted, caret or no caret.
	// biome-ignore lint/correctness/useExhaustiveDependencies: a submit asks for a fresh look.
	useEffect(() => {
		const view = viewRef.current;
		if (!view || dirtyRef.current) return;
		if (view.state.doc.toString() === value) return;
		view.dispatch({
			changes: { from: 0, to: view.state.doc.length, insert: value },
			annotations: [inbound.of(true), Transaction.addToHistory.of(false)],
		});
	}, [value, submits]);

	useEffect(() => {
		viewRef.current?.dispatch({ effects: slots.mode.reconfigure(modeFor(readOnly)) });
	}, [readOnly, modeFor, slots]);

	useEffect(() => {
		viewRef.current?.dispatch({ effects: slots.gutter.reconfigure(showNumbers ? codeGutter : []) });
	}, [showNumbers, slots]);

	useEffect(() => {
		viewRef.current?.dispatch({
			effects: slots.wrap.reconfigure(wrap ? EditorView.lineWrapping : []),
		});
	}, [wrap, slots]);

	// -- diff --------------------------------------------------------------
	//
	// Runs after the inbound value above, so a write that moves both texts
	// lands the new doc first and then diffs it once. Emptied, then filled
	// fresh: see "Diff" in the header.
	const armDiff = useCallback(() => {
		const view = viewRef.current;
		const against = cb.current.original;
		// A plain code view never had a diff, so it pays nothing here.
		if (!view || (against == null && !armedRef.current)) return;
		view.dispatch({ effects: slots.diff.reconfigure([]) });
		armedRef.current = against != null;
		if (against != null) view.dispatch({ effects: slots.diff.reconfigure(diffAgainst(against)) });
	}, [slots]);

	// biome-ignore lint/correctness/useExhaustiveDependencies: either text moving redraws the diff.
	useEffect(() => {
		armDiff();
	}, [original, value, armDiff]);

	useEffect(() => {
		let live = true;
		loadLanguage(language).then((support) => {
			if (!live) return;
			viewRef.current?.dispatch({ effects: slots.language.reconfigure(support ?? []) });
			// Removed lines take their highlighting from the language when they
			// are drawn, so a diff drawn before the language landed is redrawn.
			if (cb.current.original != null) armDiff();
		});
		return () => {
			live = false;
		};
	}, [language, slots, armDiff]);

	const bounds = {
		"--nu-code-min": minHeight > 0 ? `${minHeight}px` : "0",
		"--nu-code-max": maxHeight > 0 ? `${maxHeight}px` : "none",
	} as React.CSSProperties;

	return <div ref={hostRef} className={className} style={bounds} />;
}
