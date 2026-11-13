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
// ## Markdown editors by path
//
// A host that owns a sequence of nodes (a page of cells) finds the markdown
// editor inside one of them by path and talks to it through its handle
// (../../lib/markdown/handle.ts), whoever drew the node around it: no DOM
// queries, no selectors, nothing that depends on how the node was drawn. So
// this node keeps one table of the editors it has mounted, by path, and
// what each one takes:
//
//   - registerMarkdown: the editor joins on mount and leaves on teardown,
//     and in between says whether it takes commands (`editable(handle)`)
//     or is read-only (`editable(null)`).
//   - markdownAt: null when no markdown editor is mounted at or under a
//     path; `{ handle: null }` when one is, read-only; `{ handle }` when it
//     takes commands.
//   - subscribeMarkdown: hear editors appear, change and leave under a path.
//
// A program opens an editor in steps, the text first and editing a frame
// later, so a fresh one is mounted read-only for a moment: there, and not yet
// taking commands. A host with a request parked for it must tell that from a
// node that draws no markdown editor at all, else it gives up on every fresh
// one; hence the read-only entry. And a handle is only ever handed out while
// the editor takes commands, so a host that consumes a parked focus request
// the moment a handle appears can append and type into it.
//
// Every change is announced synchronously, inside the call that made it: a
// request parked for a node created a moment ago is consumed the moment its
// editor takes commands, not when a timer guesses it might. A plain map, like
// the type registry (../../tree/registry.ts): nothing here is rendered, so
// nothing needs a store.
//
// A host that has cut text out of one editor and put it in another wants to
// know when the second holds it for good, which is not the commit (that is
// the notify going out) but Nu's read coming back: `saved` on the handle
// waits for exactly that read.

import { OPS, type Path } from "@nustackdev/ui-core";
import type { EditorView } from "prosemirror-view";
import { useCallback, useRef } from "react";
import { Markdown } from "../../components/ui/markdown";
import type { MarkdownHandle } from "../../lib/markdown/handle";
import {
	type NodeEntry,
	type NodeProps,
	pathKey,
	useBoolProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";
import { EVENTS } from "./control";

/** A mounted markdown editor: its handle while it takes commands, null while read-only. */
export type MarkdownEntry = { handle: MarkdownHandle | null };

/** An editor appeared or changed (its entry) or left (null) at `path`. */
export type MarkdownListener = (path: Path, entry: MarkdownEntry | null) => void;

/** What a mounted editor tells the table until it leaves. */
export type MarkdownRegistration = {
	/** Takes commands through `handle`, or is read-only (null). */
	editable(handle: MarkdownHandle | null): void;
	/** Torn down. */
	leave(): void;
};

type Slot = { path: Path; handle: MarkdownHandle | null };

const editors = new Map<string, Slot>();
const listeners = new Set<{ under: Path | null; fn: MarkdownListener }>();

/** Whether `path` is `under` or inside it. Null is everywhere. */
function within(path: Path, under: Path | null): boolean {
	if (under === null) return true;
	return under.length <= path.length && under.every((seg, i) => path[i] === seg);
}

function announce(path: Path, entry: MarkdownEntry | null): void {
	for (const { under, fn } of listeners) if (within(path, under)) fn(path, entry);
}

/**
 * A markdown editor mounted at `path`, read-only until `editable` hands its
 * handle. A second registration at the same path replaces the first, whose
 * calls then do nothing, so a remount never removes its successor.
 */
export function registerMarkdown(path: Path): MarkdownRegistration {
	const key = pathKey(path);
	const slot: Slot = { path, handle: null };
	editors.set(key, slot);
	announce(path, { handle: null });
	const live = () => editors.get(key) === slot;
	return {
		editable(handle) {
			if (!live() || slot.handle === handle) return;
			slot.handle = handle;
			announce(path, { handle });
		},
		leave() {
			if (!live()) return;
			editors.delete(key);
			announce(path, null);
		},
	};
}

/**
 * The markdown editor at `path` or inside it: the first one that takes
 * commands, in registration order, else `{ handle: null }` when one is
 * mounted read-only, else null.
 */
export function markdownAt(path: Path): MarkdownEntry | null {
	let found: MarkdownEntry | null = null;
	for (const slot of editors.values()) {
		if (!within(slot.path, path)) continue;
		if (slot.handle) return { handle: slot.handle };
		found ??= { handle: null };
	}
	return found;
}

/**
 * Hear markdown editors appear, change and leave under `under` (null for all
 * of them). Returns the unsubscribe.
 */
export function subscribeMarkdown(under: Path | null, fn: MarkdownListener): () => void {
	const sub = { under, fn };
	listeners.add(sub);
	return () => {
		listeners.delete(sub);
	};
}

/** How many of its own saves a node keeps, to tell a stale echo from a write. */
const SAVES_KEPT = 8;

/**
 * What a node saved, oldest first, whether the latest has been read back,
 * and who is waiting for that read.
 */
type Saves = {
	texts: string[];
	unread: boolean;
	/** Each with what to call if the node goes before the read comes. */
	waiting: Map<() => void, (() => void) | undefined>;
};

const saves = new Map<string, Saves>();

function savesOf(path: Path): Saves {
	const key = pathKey(path);
	let s = saves.get(key);
	if (!s) {
		s = { texts: [], unread: false, waiting: new Map() };
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
function whenRead(path: Path, fn: () => void, lost?: () => void): () => void {
	const s = saves.get(pathKey(path));
	if (!s?.unread) {
		fn();
		return () => {};
	}
	s.waiting.set(fn, lost);
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
	/** This editor's place in the table; set while it is mounted. */
	const registration = useRef<MarkdownRegistration | null>(null);

	const commit = useCallback(
		(source: string) => {
			// Local first, so the read the notify provokes answers with the text
			// that provoked it.
			setValue(source);
			const s = savesOf(path);
			s.texts = [...s.texts.slice(1 - SAVES_KEPT), source];
			s.unread = true;
			send(OPS.notify, { event: EVENTS.change });
		},
		[key, setValue, send],
	);

	const stored = useCallback(
		(fn: () => void, lost?: () => void) => whenRead(path, fn, lost),
		[key],
	);

	const onView = useCallback(
		(view: EditorView | null) => {
			registration.current?.leave();
			registration.current = view ? registerMarkdown(path) : null;
		},
		[key],
	);

	const onHandle = useCallback((handle: MarkdownHandle | null) => {
		registration.current?.editable(handle);
	}, []);

	return (
		<Markdown
			value={value}
			placeholder={hint}
			readOnly={!editable}
			onCommit={commit}
			onView={onView}
			onHandle={onHandle}
			stored={stored}
		/>
	);
}

export const MarkdownRef: NodeEntry = {
	component: MarkdownView,
	fill: true,
	input: { empty: "", gathered: (props) => Boolean(props.editable) },
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
			const waiting = [...s.waiting.keys()];
			s.waiting.clear();
			for (const fn of waiting) fn();
		},
	},
	dispose: ({ path }) => {
		const s = saves.get(pathKey(path));
		saves.delete(pathKey(path));
		// Gone before the read: what was waiting for it never gets stored.
		for (const lost of s?.waiting.values() ?? []) lost?.();
	},
};
