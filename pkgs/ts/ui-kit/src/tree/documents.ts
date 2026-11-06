// Documents by tree path: how a host finds the document inside a node.
//
// A MarkdownRef registers its `DocumentHandle` (../lib/markdown/document.ts)
// at its own path while its editor is editable: it joins when the editor is
// built editable or turns editable, and leaves when it turns read-only or
// unmounts. So a registered document takes commands, always: a host that
// consumes a focus request the moment a document registers can append and
// type into it, and a document that a program has not yet opened for
// editing is not there to be asked. A host
// that owns a sequence of nodes (a page of cells) asks for the document
// under one of them by path and gets the handle, never an element: no DOM
// queries, no selectors, nothing that depends on how the node was drawn.
//
// Registration is an event the host can hear. A node created a moment ago
// has no document yet; a focus request parked for it is consumed the moment
// its document registers, not when a timer guesses it might have. So the
// registry tells its subscribers when a document appears or leaves under a
// path, synchronously, inside the registration itself.
//
// Presence is a separate question from registration. A program opens a
// document in steps, the text first and editing a frame later, so a fresh
// one is mounted read-only for a moment: it is there, and not yet taking
// commands. A host with a request parked for it must tell that from a node
// that draws no document at all, else it gives up on every fresh document.
// So an editor reports presence from mount to teardown, editable or not,
// and a host asks `documentPresent` and hears `subscribePresence`.
//
// A plain map, like the type registry (./registry.ts): nothing here is
// rendered, so nothing needs a store.

import type { Path } from "@nustackdev/ui-core";
import type { DocumentHandle } from "../lib/markdown/document";
import { pathKey } from "./hooks";

export type { DocumentHandle };

/** A document registered (handle) or left (null) at `path`. */
export type DocumentListener = (path: Path, handle: DocumentHandle | null) => void;

/** A markdown editor appeared (true) or left (false) at `path`, editable or not. */
export type PresenceListener = (path: Path, present: boolean) => void;

type Entry = { path: Path; handle: DocumentHandle };

const documents = new Map<string, Entry>();
const listeners = new Set<{ under: Path | null; fn: DocumentListener }>();
const present = new Map<string, { path: Path }>();
const presenceListeners = new Set<{ under: Path | null; fn: PresenceListener }>();

/** Whether `path` is `under` or inside it. Null is everywhere. */
function within(path: Path, under: Path | null): boolean {
	if (under === null) return true;
	return under.length <= path.length && under.every((seg, i) => path[i] === seg);
}

function announce(path: Path, handle: DocumentHandle | null): void {
	for (const { under, fn } of listeners) if (within(path, under)) fn(path, handle);
}

/**
 * Register the document at `path`. Returns the unregister. A second
 * registration at the same path replaces the first; the first's unregister
 * then does nothing, so a remount never removes its successor.
 */
export function registerDocument(path: Path, handle: DocumentHandle): () => void {
	const key = pathKey(path);
	const entry = { path, handle };
	documents.set(key, entry);
	announce(path, handle);
	return () => {
		if (documents.get(key) !== entry) return;
		documents.delete(key);
		announce(path, null);
	};
}

/** The document at `path` or inside it: the first registered, in registration order. */
export function documentUnder(path: Path): DocumentHandle | null {
	for (const entry of documents.values()) if (within(entry.path, path)) return entry.handle;
	return null;
}

/**
 * Hear documents register and leave under `path` (null for all of them).
 * Returns the unsubscribe.
 */
export function subscribeDocuments(under: Path | null, fn: DocumentListener): () => void {
	const sub = { under, fn };
	listeners.add(sub);
	return () => {
		listeners.delete(sub);
	};
}

/**
 * Report a markdown editor mounted at `path`, whether or not it takes
 * commands. Returns the unregister. A second report at the same path
 * replaces the first, whose unregister then does nothing.
 */
export function registerPresence(path: Path): () => void {
	const key = pathKey(path);
	const entry = { path };
	present.set(key, entry);
	for (const { under, fn } of presenceListeners) if (within(path, under)) fn(path, true);
	return () => {
		if (present.get(key) !== entry) return;
		present.delete(key);
		for (const { under, fn } of presenceListeners) if (within(path, under)) fn(path, false);
	};
}

/** Whether a markdown editor is mounted at `path` or inside it, editable or not. */
export function documentPresent(path: Path): boolean {
	for (const entry of present.values()) if (within(entry.path, path)) return true;
	return false;
}

/**
 * Hear markdown editors appear and leave under `path` (null for all of
 * them), editable or not. Returns the unsubscribe.
 */
export function subscribePresence(under: Path | null, fn: PresenceListener): () => void {
	const sub = { under, fn };
	presenceListeners.add(sub);
	return () => {
		presenceListeners.delete(sub);
	};
}
