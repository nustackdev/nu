// MonacoRef -- editable source. Browser is source of truth while you type.
//
// The value is the text, both ways. Commit moments (cmd+enter, blur): the
// node's `value` prop updates locally, then a notify goes out and the server
// reads back. A server-initiated write replaces the source, and needs a handler
// for the InputRef reason: nil must land as "" so the editor never sees null
// and a following read answers "". The map form merges
// {value, language, read_only, min_height, max_height} the way the store merges
// everything else.
//
// Sibling to CodeBlockRef, which shows the same text read-only and costs no
// editor. Reach for this one only when the text is meant to be edited: Monaco
// is a large chunk and the first node that mounts pays for it.
//
// The editor itself (loading, theming, the Monaco wiring) lives in ./monaco/ --
// no store coupling, so a host that wants a code box without a node can use it
// directly.

import { OPS } from "@nustackdev/ui-core";
import { useCallback } from "react";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useNumberProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";
import { MonacoEditor } from "./monaco/editor";

function MonacoView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const language = useStringProp(path, "language", "python");
	const readOnly = useBoolProp(path, "read_only");
	const minHeight = useNumberProp(path, "min_height", 42);
	const maxHeight = useNumberProp(path, "max_height", 560);
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
		<MonacoEditor
			value={value}
			language={language}
			readOnly={readOnly}
			minHeight={minHeight}
			maxHeight={maxHeight}
			onCommit={commit}
		/>
	);
}

export const MonacoRef: NodeEntry = {
	component: MonacoView,
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
