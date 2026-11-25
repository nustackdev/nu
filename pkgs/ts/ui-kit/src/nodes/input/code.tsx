// CodeRef -- source code, read-only by default, editable on request.
//
// One node for both faces of a code surface. Read-only it is a highlighted
// block with a copy button; with `readonly` off it is an editor, and the
// browser is source of truth while you type. `readonly` is true when unset,
// and a disabled Fieldset or Form around it makes it read-only too. Renders the kit's `Code` block,
// one engine either way, so flipping the flag never changes how the code looks.
//
// `original` set (a string, "" included) makes it a diff: `value` shown as a
// unified diff against the old text, read-only whatever `readonly` says, and
// never gathered by a Form since nobody types into it. Nil turns the diff off.
// A write to either text redraws the diff in the same view.
//
// Commit moments (the send key, blur, only when the text changed): the
// node's `value` prop updates locally, then `{event: "change", value}` goes
// out with the text. Between commits each keystroke sends `{event: "input",
// value}` with the editor's text, built only when someone listens, while
// `value` keeps the last commit. A read answers what the editor shows, the
// edits included (./draft.ts), the same text an input event carries. The send key also sends `{event: "submit", value}`
// after its commit, asks an enclosing Form to submit, and with
// `clear_on_submit` puts the declared value back, the editor's document
// included (./control.ts `useSubmit`). `submit_on` picks the key, shift+Enter
// (default, Enter the newline) or Enter, the same switch as every multi-line
// input. A server-initiated write replaces the source, and needs a handler
// for the InputRef reason: nil must land as "" so the view never sees null
// and a following read answers "". The map form merges {value, original,
// language, readonly, line_numbers, wrap, show_copy, min_height, max_height,
// submit_on, clear_on_submit} the way the store merges everything else.

import type { EditorView } from "@codemirror/view";
import { useCallback, useEffect, useRef } from "react";
import { Code } from "../../components/ui/code";
import { SUBMIT_ON } from "../../lib/keyboard";
import {
	isWatched,
	type NodeEntry,
	type NodeProps,
	pathKey,
	useBoolProp,
	useEmit,
	useEnumProp,
	useNumberProp,
	useProps,
	useSetValue,
	useStringProp,
} from "../../tree";
import { EVENTS, resetHandler, useDisabledScope, useSubmit } from "./control";
import { clearDraft, readDraft, setDraft } from "./draft";

function CodeView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const language = useStringProp(path, "language");
	// Raw, not useStringProp: "" is a diff against nothing, nil is no diff.
	const raw = useProps(path).original;
	const original = typeof raw === "string" ? raw : undefined;
	const scoped = useDisabledScope();
	const readOnly = useBoolProp(path, "readonly", true) || scoped;
	const submitOn = useEnumProp(path, "submit_on", SUBMIT_ON, "shift+enter");
	// Nil means "follow the mode": numbered while editable, bare while reading.
	const numbers = useProps(path).line_numbers;
	const wrap = useBoolProp(path, "wrap");
	const showCopy = useBoolProp(path, "show_copy", true);
	const minHeight = useNumberProp(path, "min_height", 0);
	const maxHeight = useNumberProp(path, "max_height", 0);
	const setValue = useSetValue(path);
	const emit = useEmit(path);
	const key = pathKey(path);
	/** The editor, so a draft reads its text as it stands. */
	const view = useRef<EditorView | null>(null);
	const onView = useCallback((v: EditorView | null) => {
		view.current = v;
	}, []);

	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
	useEffect(() => () => clearDraft(path), [key]);

	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
	const commit = useCallback(
		(source: string) => {
			// Local first, so a read after the notify answers with the text it carried.
			clearDraft(path);
			setValue(source);
			emit(EVENTS.change, { value: source });
		},
		[key, setValue, emit],
	);

	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
	const edit = useCallback(
		(read: () => string) => {
			setDraft(path, () => view.current?.state.doc.toString() ?? read());
			if (isWatched(path, EVENTS.input)) emit(EVENTS.input, { value: read() });
		},
		[key, emit],
	);

	const fire = useSubmit(path);
	const submit = useCallback(() => fire(document.activeElement), [fire]);

	return (
		<Code
			block
			value={value}
			language={language}
			original={original}
			readOnly={readOnly}
			lineNumbers={numbers == null ? undefined : Boolean(numbers)}
			wrap={wrap}
			copyable={showCopy}
			minHeight={minHeight}
			maxHeight={maxHeight}
			onCommit={commit}
			onEdit={edit}
			onView={onView}
			onSubmit={submit}
			submitOn={submitOn}
		/>
	);
}

export const CodeRef: NodeEntry = {
	component: CodeView,
	fill: true,
	input: {
		empty: "",
		gathered: (props) => props.readonly === false && typeof props.original !== "string",
	},
	handlers: {
		read: readDraft,
		reset: resetHandler,
		write: (ctx, payload) =>
			ctx.update((props) => {
				// Scalar form: a bare string (or nil) replaces just the source.
				if (payload == null || typeof payload === "string") {
					props.value = payload == null ? "" : payload;
					return;
				}
				if (typeof payload === "object" && !Array.isArray(payload)) {
					Object.assign(props, payload);
					if ("value" in payload) {
						props.value = props.value == null ? "" : String(props.value);
					}
				}
			}),
	},
};
