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
//
// ## Saves that come back
//
// A program that keeps the text (nuverse's text cell does) writes it back to
// this node after each read, so every save returns as an inbound write, and
// not necessarily in step: save v1, then type and save v2, and v1's echo can
// land after v2 is on the screen. Adopted, it would roll the screen back to
// v1; worse, the read that follows v2's notify is answered from this node's
// `value`, so the program would store v1 and v2 would be gone for good. So
// this node, the one layer that sees both its own saves go out and the
// frames come in, keeps the texts it saved: an inbound value that is an
// earlier save of its own, not the latest, is a stale echo and leaves `value`
// alone. And a read that arrives while a save has gone out and not been read
// back yet is answered with that save, whatever has landed in `value`
// meanwhile, since that save is what the read was provoked by. Nothing is
// held back: a program's write that is not one of these echoes lands at
// once, so a program that never writes the text back works as it always did.
//
// The document registers its handle at the node's path while it is editable
// (../../tree/documents.ts), so a host that owns a sequence of nodes can
// find it and talk to it by path, whoever drew the node around it; and it
// reports its presence from mount to teardown, editable or not, so a host
// can tell a document that is not yet open for editing from no document. A host
// that has cut text out of one document and put it in another wants to know
// when the second holds it for good, which is not the commit (that is the
// notify going out) but Nu's read coming back: `saved` on the handle waits
// for exactly that read.

import { OPS, type Path } from "@nustackdev/ui-core";
import type { EditorView } from "prosemirror-view";
import { useCallback, useRef } from "react";
import { Markdown } from "../../components/ui/markdown";
import type { DocumentHandle } from "../../lib/markdown/document";
import {
	type NodeEntry,
	type NodeProps,
	pathKey,
	registerDocument,
	registerPresence,
	useBoolProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

/** How many of its own saves a node keeps, to tell a stale echo from a write. */
const SAVES_KEPT = 8;

/**
 * What a node saved, oldest first, whether the latest has been read back,
 * and who is waiting for that read.
 */
type Saves = { texts: string[]; unread: boolean; waiting: Set<() => void> };

const saves = new Map<string, Saves>();

function savesOf(path: Path): Saves {
	const key = pathKey(path);
	let s = saves.get(key);
	if (!s) {
		s = { texts: [], unread: false, waiting: new Set() };
		saves.set(key, s);
	}
	return s;
}

/** The source a write payload carries, in the editor's own form, or undefined when it carries none. */
function sourceOf(payload: unknown): string | undefined {
	if (payload == null || typeof payload === "string") return payload == null ? "" : payload;
	if (typeof payload === "object" && !Array.isArray(payload) && "value" in payload) {
		const v = (payload as { value: unknown }).value;
		return v == null ? "" : String(v);
	}
	return undefined;
}

/** `fn` once the latest save has been read back: now if it has, else at that read. */
function whenRead(path: Path, fn: () => void): () => void {
	const s = saves.get(pathKey(path));
	if (!s?.unread) {
		fn();
		return () => {};
	}
	s.waiting.add(fn);
	return () => {
		s.waiting.delete(fn);
	};
}

function MarkdownView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const hint = useStringProp(path, "placeholder");
	const editable = useBoolProp(path, "editable");
	const setValue = useSetValue(path);
	const send = useSend(path);
	const key = pathKey(path);
	/** Leaves the registry; set while the document is registered. */
	const leave = useRef<(() => void) | null>(null);
	/** Withdraws presence; set while the editor is mounted. */
	const leavePresence = useRef<(() => void) | null>(null);

	const commit = useCallback(
		(source: string) => {
			// Local first, so the read the notify provokes answers with the text
			// that provoked it.
			setValue(source);
			const s = savesOf(path);
			s.texts = [...s.texts.slice(1 - SAVES_KEPT), source];
			s.unread = true;
			send(OPS.notify);
		},
		[key, setValue, send],
	);

	const stored = useCallback((fn: () => void) => whenRead(path, fn), [key]);

	const onView = useCallback(
		(view: EditorView | null) => {
			leavePresence.current?.();
			leavePresence.current = view ? registerPresence(path) : null;
		},
		[key],
	);

	const onDocument = useCallback(
		(handle: DocumentHandle | null) => {
			leave.current?.();
			leave.current = handle ? registerDocument(path, handle) : null;
		},
		[key],
	);

	return (
		<Markdown
			value={value}
			placeholder={hint}
			readOnly={!editable}
			onCommit={commit}
			onView={onView}
			onDocument={onDocument}
			stored={stored}
		/>
	);
}

export const MarkdownRef: NodeEntry = {
	component: MarkdownView,
	fill: true,
	handlers: {
		write: (ctx, payload) => {
			const source = sourceOf(payload);
			const s = saves.get(pathKey(ctx.path));
			// A stale echo: one of this node's own earlier saves, not its latest.
			const stale =
				source !== undefined && s !== undefined && source !== s.texts[s.texts.length - 1]
					? s.texts.includes(source)
					: false;
			ctx.update((props) => {
				// Scalar form: a bare string (or nil) replaces just the source.
				if (payload == null || typeof payload === "string") {
					if (!stale) props.value = source;
					return;
				}
				if (typeof payload === "object" && !Array.isArray(payload)) {
					const { value: _value, ...rest } = payload as Record<string, unknown>;
					Object.assign(props, rest);
					if (source !== undefined && !stale) props.value = source;
				}
			});
		},
		read: (ctx) => {
			// A save that has gone out and not been read back yet is what this
			// read is for, whatever landed in `value` since.
			const s = saves.get(pathKey(ctx.path));
			const pending = s?.unread ? s.texts[s.texts.length - 1] : undefined;
			ctx.send(OPS.read, pending ?? ctx.node.props.value ?? null, ctx.frame.id);
			if (!s?.unread) return;
			s.unread = false;
			const waiting = [...s.waiting];
			s.waiting.clear();
			for (const fn of waiting) fn();
		},
	},
	dispose: ({ path }) => {
		saves.delete(pathKey(path));
	},
};
