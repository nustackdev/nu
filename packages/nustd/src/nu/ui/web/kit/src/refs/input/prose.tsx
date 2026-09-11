// ProseRef -- editable rich text. Browser is source of truth while you type.
//
// The value is a markdown string, both ways. The browser renders it as a live
// document and never shows the source; the server writes and reads the same
// string it always did. Sibling to MarkdownRef, which renders the same dialect
// read-only and costs no editor.
//
// Commit moments (a quiet moment, blur): notify the server, which reads back.
// Server-initiated write: scalar form replaces the source; map form merges any
// subset of {value, placeholder, read_only}.
//
// Last actor wins. No OT, no CRDT: two people in one Ref clobber each other,
// and that is the contract, not a gap.

import { OP_NOTIFY } from "@nustackdev/ui-core";
import { useCallback } from "react";
import { Prose } from "../../components/ui/prose";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";
import { ProseEditor } from "./prose/editor";

const factory: SliceFactory = (path, ctx, props) => ({
	type: "ProseRef",
	value: typeof props?.value === "string" ? (props.value as string) : "",
	placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
	read_only: typeof props?.read_only === "boolean" ? (props.read_only as boolean) : false,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			// Scalar form: a bare string (or nil) replaces just the source.
			if (v == null || typeof v === "string") {
				slice.value = v == null ? "" : v;
				return;
			}
			const p = v as { value?: unknown; placeholder?: unknown; read_only?: unknown };
			if ("value" in p) slice.value = p.value == null ? "" : String(p.value);
			if ("placeholder" in p) slice.placeholder = String(p.placeholder ?? "");
			if ("read_only" in p) slice.read_only = Boolean(p.read_only);
		}),
	get: () => {
		const slice = useStore.getState().refs[path];
		return (slice?.value as string) ?? "";
	},
});

function ProseView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	const hint = useStore((s) => (s.refs[path]?.placeholder as string) ?? "");
	const readOnly = useStore((s) => Boolean(s.refs[path]?.read_only));
	const setLocal = useStore((s) => s.setLocal);
	const send = useStore((s) => s.send);

	const commit = useCallback(
		(source: string) => {
			// Local first, so the read the notify provokes answers with the text
			// that provoked it.
			setLocal(path, source);
			send({ op: OP_NOTIFY, ref: path, payload: null });
		},
		[path, setLocal, send],
	);

	return (
		<Prose>
			<ProseEditor value={value} placeholder={hint} readOnly={readOnly} onCommit={commit} />
		</Prose>
	);
}

export const ProseRef: RefEntry = { factory, component: ProseView };
