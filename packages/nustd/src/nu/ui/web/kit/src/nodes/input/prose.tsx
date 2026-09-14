// ProseRef -- editable rich text. Browser is source of truth while you type.
//
// The value is a markdown string, both ways. The browser renders it as a live
// document and never shows the source; the server writes and reads the same
// string it always did. Sibling to MarkdownRef, which renders the same dialect
// read-only and costs no editor.
//
// Commit moments (a quiet moment, blur): the node's `value` prop updates
// locally, then a notify goes out and the server reads back. A server-initiated
// write replaces the source, and needs a handler for the InputRef reason: nil
// must land as "" so the editor never sees null and a following read answers
// "". The map form merges {value, placeholder, read_only} the way the store
// merges everything else.
//
// Last actor wins. No OT, no CRDT: two people in one node clobber each other,
// and that is the contract, not a gap.
//
// The editor itself (schema, markdown, rules) lives in ./prose/ -- pure
// editor machinery, no store coupling, so it survived the tree port
// untouched.

import { OPS } from "@nustackdev/ui-core";
import { useCallback } from "react";
import { Prose } from "../../components/ui/prose";
import { ProseEditor } from "./prose/editor";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

function ProseView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const hint = useStringProp(path, "placeholder");
	const readOnly = useBoolProp(path, "read_only");
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
		<Prose>
			<ProseEditor value={value} placeholder={hint} readOnly={readOnly} onCommit={commit} />
		</Prose>
	);
}

export const ProseRef: NodeEntry = {
	component: ProseView,
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
