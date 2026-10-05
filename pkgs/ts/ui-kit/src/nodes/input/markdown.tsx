// MarkdownRef -- a markdown document, read-only by default, editable on request.
//
// One node for both faces of a document. The value is a markdown string both
// ways, and the browser never shows the source: read-only it renders the
// document, with `editable` on it is a live wysiwyg editor and the browser is
// source of truth while you type. Renders the kit's `Markdown` primitive, one
// engine either way, so what a document looks like never depends on whether
// you can type in it.
//
// Commit moments (a quiet moment, blur): the node's `value` prop updates
// locally, then a notify goes out and the server reads back. A server-initiated
// write replaces the source, and needs a handler for the InputRef reason: nil
// must land as "" so the editor never sees null and a following read answers
// "". The map form merges {value, placeholder, editable} the way the store
// merges everything else.
//
// Last actor wins. No OT, no CRDT: two people in one node clobber each other,
// and that is the contract, not a gap.

import { OPS } from "@nustackdev/ui-core";
import { useCallback } from "react";
import { Markdown } from "../../components/ui/markdown";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

function MarkdownView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const hint = useStringProp(path, "placeholder");
	const editable = useBoolProp(path, "editable");
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

	return <Markdown value={value} placeholder={hint} readOnly={!editable} onCommit={commit} />;
}

export const MarkdownRef: NodeEntry = {
	component: MarkdownView,
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
