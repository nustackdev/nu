// CodeRef -- source code, read-only by default, editable on request.
//
// One node for both faces of a code surface. Read-only it is a highlighted
// block with a copy button; with `editable` on it is an editor, and the
// browser is source of truth while you type. Renders the kit's `Code` block,
// one engine either way, so flipping the flag never changes how the code looks.
//
// Commit moments (cmd+enter, blur): the node's `value` prop updates locally,
// then a notify goes out and the server reads back. A server-initiated write
// replaces the source, and needs a handler for the InputRef reason: nil must
// land as "" so the view never sees null and a following read answers "". The
// map form merges {value, language, editable, line_numbers, wrap, show_copy,
// min_height, max_height} the way the store merges everything else.

import { OPS } from "@nustackdev/ui-core";
import { useCallback } from "react";
import { Code } from "../../components/ui/code";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useNumberProp,
	useProps,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

function CodeView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const language = useStringProp(path, "language");
	const editable = useBoolProp(path, "editable");
	// Nil means "follow the mode": numbered while editable, bare while reading.
	const numbers = useProps(path).line_numbers;
	const wrap = useBoolProp(path, "wrap");
	const showCopy = useBoolProp(path, "show_copy", true);
	const minHeight = useNumberProp(path, "min_height", 0);
	const maxHeight = useNumberProp(path, "max_height", 0);
	const setValue = useSetValue(path);
	const send = useSend(path);

	const commit = useCallback(
		(source: string) => {
			// Local first, so the read the notify provokes answers with the text
			// that provoked it.
			setValue(source);
			send(OPS.notify);
		},
		[setValue, send],
	);

	return (
		<Code
			block
			value={value}
			language={language}
			readOnly={!editable}
			lineNumbers={numbers == null ? undefined : Boolean(numbers)}
			wrap={wrap}
			copyable={showCopy}
			minHeight={minHeight}
			maxHeight={maxHeight}
			onCommit={commit}
		/>
	);
}

export const CodeRef: NodeEntry = {
	component: CodeView,
	handlers: {
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
