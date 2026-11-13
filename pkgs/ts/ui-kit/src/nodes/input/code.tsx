// CodeRef -- source code, read-only by default, editable on request.
//
// One node for both faces of a code surface. Read-only it is a highlighted
// block with a copy button; with `readonly` off it is an editor, and the
// browser is source of truth while you type. `readonly` is true when unset,
// and a disabled Fieldset or Form around it makes it read-only too. Renders the kit's `Code` block,
// one engine either way, so flipping the flag never changes how the code looks.
//
// Commit moments (cmd+enter, blur, only when the text changed): the node's
// `value` prop updates locally, then `{event: "change"}` goes out and the
// server reads back. cmd+enter also sends `{event: "submit"}` after its
// commit, and asks an enclosing Form to submit (./control.ts). A server-initiated write
// replaces the source, and needs a handler for the InputRef reason: nil must
// land as "" so the view never sees null and a following read answers "". The
// map form merges {value, language, readonly, line_numbers, wrap, show_copy,
// min_height, max_height} the way the store merges everything else.

import { OPS } from "@nustackdev/ui-core";
import { useCallback } from "react";
import { Code } from "../../components/ui/code";
import {
	type NodeEntry,
	type NodeProps,
	pathKey,
	useBoolProp,
	useNumberProp,
	useProps,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";
import { EVENTS, requestFormSubmit, resetHandler, submitted, useDisabledScope } from "./control";

function CodeView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const language = useStringProp(path, "language");
	const scoped = useDisabledScope();
	const readOnly = useBoolProp(path, "readonly", true) || scoped;
	// Nil means "follow the mode": numbered while editable, bare while reading.
	const numbers = useProps(path).line_numbers;
	const wrap = useBoolProp(path, "wrap");
	const showCopy = useBoolProp(path, "show_copy", true);
	const minHeight = useNumberProp(path, "min_height", 0);
	const maxHeight = useNumberProp(path, "max_height", 0);
	const setValue = useSetValue(path);
	const send = useSend(path);
	const key = pathKey(path);

	const commit = useCallback(
		(source: string) => {
			// Local first, so the read the notify provokes answers with the text
			// that provoked it.
			setValue(source);
			send(OPS.notify, { event: EVENTS.change });
		},
		[setValue, send],
	);

	const submit = useCallback(
		() => {
			send(OPS.notify, { event: EVENTS.submit, value: submitted(path) });
			requestFormSubmit(document.activeElement);
		},
		// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
		[key, send],
	);

	return (
		<Code
			block
			value={value}
			language={language}
			readOnly={readOnly}
			lineNumbers={numbers == null ? undefined : Boolean(numbers)}
			wrap={wrap}
			copyable={showCopy}
			minHeight={minHeight}
			maxHeight={maxHeight}
			onCommit={commit}
			onSubmit={submit}
		/>
	);
}

export const CodeRef: NodeEntry = {
	component: CodeView,
	fill: true,
	input: { empty: "", gathered: (props) => props.readonly === false },
	handlers: {
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
