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
// Not every keystroke. Cmd+enter is the deliberate save and blur is the
// accidental one, and a commit that round-trips to the same text is dropped.
// `onDirty` is the live read in between, for a host that wants to show an
// unsaved marker.
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

import {
	Annotation,
	Compartment,
	EditorState,
	type Extension,
	Transaction,
} from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import type * as React from "react";
import { useCallback, useEffect, useLayoutEffect, useRef } from "react";
import { codeBase, codeEditing, codeGutter, codeReading } from "./extensions";
import { loadLanguage } from "./languages";

export type CodeMirrorViewProps = {
	/** The source. Owned by whoever renders this. */
	value: string;
	/** A language name or alias (`python`, `ts`, `sql`, `shell`). Unknown renders plain. */
	language?: string;
	/** On by default: a code view reads unless told it may be edited. */
	readOnly?: boolean;
	/** Defaults to on while editable, off while read-only. */
	lineNumbers?: boolean;
	/** Soft-wrap long lines instead of scrolling sideways. */
	wrap?: boolean;
	/** Height bounds in px. The view grows with its content between them; 0 is no bound. */
	minHeight?: number;
	maxHeight?: number;
	/** Persist. Fires on cmd+enter and on blur, and only when the text changed. */
	onCommit?: (source: string) => void;
	/** Whether the buffer differs from `value`, on every keystroke. */
	onDirty?: (dirty: boolean) => void;
	className?: string;
	/**
	 * Handed the live view on mount and null on teardown. The escape hatch for
	 * a host that needs to bind keys or drive the caret from above.
	 */
	onView?: (view: EditorView | null) => void;
};

/** Marks a transaction as the inbound value landing, not a keystroke. */
const inbound = Annotation.define<boolean>();

/** The editing set, with this view's own undo stack and its deliberate-save key. */
function editing(commit: () => void): Extension {
	return codeEditing({
		history: true,
		keys: [
			{
				key: "Mod-Enter",
				run: () => {
					commit();
					return true;
				},
			},
		],
	});
}

export function CodeMirrorView({
	value,
	language = "",
	readOnly = true,
	lineNumbers: numbered,
	wrap = false,
	minHeight = 0,
	maxHeight = 0,
	onCommit,
	onDirty,
	className,
	onView,
}: CodeMirrorViewProps) {
	const hostRef = useRef<HTMLDivElement | null>(null);
	const viewRef = useRef<EditorView | null>(null);
	/** The buffer changed since the last commit or inbound value. Gates inbound writes. */
	const dirtyRef = useRef(false);
	// The view binds its listeners once, so everything they read goes through
	// a ref rather than a closed-over prop.
	const cb = useRef({ value, onCommit, onDirty, onView });
	cb.current = { value, onCommit, onDirty, onView };

	const showNumbers = numbered ?? !readOnly;

	const slots = useRef({
		mode: new Compartment(),
		language: new Compartment(),
		gutter: new Compartment(),
		wrap: new Compartment(),
	}).current;

	const commit = useCallback(() => {
		const view = viewRef.current;
		if (!view) return;
		dirtyRef.current = false;
		const next = view.state.doc.toString();
		if (next === cb.current.value) return;
		cb.current.onCommit?.(next);
	}, []);

	const modeFor = useCallback((ro: boolean) => (ro ? codeReading : editing(commit)), [commit]);

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
					codeBase,
					EditorView.updateListener.of((u) => {
						if (u.docChanged && u.transactions.some((tr) => !tr.annotation(inbound))) {
							dirtyRef.current = true;
							cb.current.onDirty?.(u.state.doc.toString() !== cb.current.value);
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
	useEffect(() => {
		const view = viewRef.current;
		if (!view || dirtyRef.current) return;
		if (view.state.doc.toString() === value) return;
		view.dispatch({
			changes: { from: 0, to: view.state.doc.length, insert: value },
			annotations: [inbound.of(true), Transaction.addToHistory.of(false)],
		});
	}, [value]);

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

	useEffect(() => {
		let live = true;
		loadLanguage(language).then((support) => {
			if (!live) return;
			viewRef.current?.dispatch({ effects: slots.language.reconfigure(support ?? []) });
		});
		return () => {
			live = false;
		};
	}, [language, slots]);

	const bounds = {
		"--nu-code-min": minHeight > 0 ? `${minHeight}px` : "0",
		"--nu-code-max": maxHeight > 0 ? `${maxHeight}px` : "none",
	} as React.CSSProperties;

	return <div ref={hostRef} className={className} style={bounds} />;
}
