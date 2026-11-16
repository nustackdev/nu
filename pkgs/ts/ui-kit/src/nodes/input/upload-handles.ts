// The browser half of an upload node: the files a person handed over, and
// the commands the program sends about them.
//
// Picking a file moves no bytes. The node keeps a handle per file in a map of
// its own, `key -> {file, token, transfer, state, sent}`, keyed by a key
// minted here at pick time. The value the program reads is one plain dict
// per file (`{key, name, mime, size, modified, state, sent, error}`), never
// the handle: a `File` cannot cross the wire, and the program keeps no state
// of its own, so the browser is the one place that knows what landed where.
//
// Every byte goes over http (lib/transfer), never the ws. The program asks
// with a command on the node's path and hears back a `notify` there:
//
//   pull        {key, rid, url}              -> upload {key, rid, token, state, size, error}
//                                               progress {key, rid, sent, size} on the way
//   slice       {key, rid, url, start, end}  -> slice {key, rid, token, cached, state, size, error}
//   cancel      {key}                        -> the running pull ends with upload, state canceled
//   discard     {key, rid}                   -> discard {key, rid, token}
//   remove_file {key}                        -> nothing; the value moves
//
// `key` names the file: the key from the value, or an index into the value
// (how `file(i)` names its entry; the index is turned into a key here, at
// request time). Null on the one file node means its file; on the files node
// a null `pull` or `cancel` means every file.
//
// A pull of a file already landed answers at once with the token it has; a
// pull of one on its way waits with it and answers when it ends. A slice of a
// landed file answers `cached: true` and sends nothing: the program reads the
// range from the file it already has. Progress is throttled here: at most
// every 100 ms and only when it moved by 1% of the file.
//
// Program side moves (a reset, a `remove_file`) send no change, as no input
// echoes what the program did; a person's pick, drop, paste or remove does.

import { type NodeHandler, OPS, type Path } from "@nustackdev/ui-core";
import type { FileState } from "../../components/ui/file-input";
import { postBlob, type Transfer, type TransferResult } from "../../lib/transfer";
import { nodeAt, pathKey, tree } from "../../tree";
import { resetInput } from "./control";

export type { FileState };

/** One file as the program reads it. */
export type FileValue = {
	key: string;
	name: string;
	mime: string;
	size: number;
	modified: number;
	state: FileState;
	sent: number;
	error: string;
};

type Handle = {
	key: string;
	file: File;
	token: string | null;
	state: FileState;
	sent: number;
	error: string;
	/** The running pull, if any. */
	pull: Transfer | null;
	/** The rid the running pull started with; its progress carries it. */
	rid: string | null;
	/** Every rid waiting on the running pull, answered when it ends. */
	waiters: string[];
	/** Slices on their way, aborted with the file. */
	slices: Set<Transfer>;
	/** The last progress sent: when, and how far. */
	reportedAt: number;
	reported: number;
};

/** At most one progress notify per file per this many ms. */
export const PROGRESS_MS = 100;
/** And only when it moved by this share of the file. */
export const PROGRESS_STEP = 0.01;

export const FILES_TYPE = "UploadFilesRef";

/** Every upload node's handles, by node path. */
const books = new Map<string, Map<string, Handle>>();

function book(path: Path): Map<string, Handle> {
	const at = pathKey(path);
	let found = books.get(at);
	if (!found) {
		found = new Map();
		books.set(at, found);
	}
	return found;
}

function isFiles(path: Path): boolean {
	return nodeAt(path)?.type === FILES_TYPE;
}

let minted = 0;

/** A key for a new pick: unique in this tab, never all digits. */
function mintKey(): string {
	minted += 1;
	return `f${Date.now().toString(36)}${minted.toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

function entry(h: Handle): FileValue {
	return {
		key: h.key,
		name: h.file.name,
		mime: h.file.type,
		size: h.file.size,
		modified: h.file.lastModified,
		state: h.state,
		sent: h.sent,
		error: h.error,
	};
}

/** The node's value from its handles: a dict or null, or a list. */
export function filesValue(path: Path): FileValue | FileValue[] | null {
	const all = [...book(path).values()].map(entry);
	return isFiles(path) ? all : (all[0] ?? null);
}

/** Put the handles' state in the value. Sends nothing: a pull state is not a change. */
function land(path: Path): void {
	if (!nodeAt(path)) return;
	tree.getState().setProps(path, { value: filesValue(path) });
}

function notify(path: Path, payload: Record<string, unknown>): void {
	tree.getState().send({ op: OPS.notify, ref: path, payload });
}

/** Stop everything a handle has on its way. Waiters hear `canceled`. */
function release(h: Handle): void {
	h.pull?.abort();
	for (const s of h.slices) s.abort();
}

/**
 * Take files a person handed over: new handles, appended, or in place of
 * what was there when `replace`. Returns the new value; the caller sends the
 * change.
 */
export function addFiles(path: Path, files: File[], replace: boolean): unknown {
	const b = book(path);
	if (replace) {
		for (const h of b.values()) release(h);
		b.clear();
	}
	for (const file of files) {
		const key = mintKey();
		b.set(key, {
			key,
			file,
			token: null,
			state: "picked",
			sent: 0,
			error: "",
			pull: null,
			rid: null,
			waiters: [],
			slices: new Set(),
			reportedAt: Number.NEGATIVE_INFINITY,
			reported: 0,
		});
	}
	return filesValue(path);
}

/** Drop one file. Returns the new value. */
export function removeFile(path: Path, key: string): unknown {
	const b = book(path);
	const h = b.get(key);
	if (h) {
		b.delete(key);
		release(h);
	}
	return filesValue(path);
}

/** Drop every file of a node and forget it (the node went away). */
export function dropFiles(path: Path): void {
	const at = pathKey(path);
	const b = books.get(at);
	if (!b) return;
	books.delete(at);
	for (const h of b.values()) release(h);
}

/**
 * Drop the handles the value no longer names. A Form's reset puts the value
 * back without asking the node, so the handles follow the value here.
 */
export function prune(path: Path): void {
	const b = books.get(pathKey(path));
	if (!b) return;
	const raw = nodeAt(path)?.props.value;
	const list = Array.isArray(raw) ? raw : raw ? [raw] : [];
	const named = new Set(list.map((v) => (v as { key?: unknown })?.key));
	for (const [key, h] of b) {
		if (named.has(key)) continue;
		b.delete(key);
		release(h);
	}
}

/** The handle a command names, by key or by index into the value. */
function target(path: Path, key: unknown): Handle | null {
	prune(path);
	const b = book(path);
	if (typeof key === "string") return b.get(key) ?? null;
	if (typeof key === "number" && Number.isInteger(key)) {
		const all = [...b.values()];
		return all[key < 0 ? all.length + key : key] ?? null;
	}
	if (key == null && !isFiles(path)) return b.values().next().value ?? null;
	return null;
}

/** The handles a pull or cancel names: one, or every file for a null key on the files node. */
function targets(path: Path, key: unknown): Handle[] {
	if (key == null && isFiles(path)) {
		prune(path);
		return [...book(path).values()];
	}
	const one = target(path, key);
	return one ? [one] : [];
}

function live(path: Path, h: Handle): boolean {
	return books.get(pathKey(path))?.get(h.key) === h;
}

type Fields = Record<string, unknown>;

function fields(payload: unknown): Fields {
	return payload && typeof payload === "object" && !Array.isArray(payload)
		? (payload as Fields)
		: {};
}

function str(v: unknown): string | null {
	return typeof v === "string" && v !== "" ? v : null;
}

function asIndex(v: unknown, size: number, fallback: number): number {
	if (typeof v !== "number" || !Number.isFinite(v)) return fallback;
	const at = Math.trunc(v);
	return Math.min(size, Math.max(0, at < 0 ? size + at : at));
}

// --- progress ----------------------------------------------------------------

function progressed(path: Path, h: Handle, sent: number): void {
	if (!live(path, h) || h.state !== "pulling") return;
	h.sent = sent;
	const size = h.file.size;
	const now = Date.now();
	if (now - h.reportedAt < PROGRESS_MS) return;
	if (size <= 0 || sent - h.reported < size * PROGRESS_STEP) return;
	h.reportedAt = now;
	h.reported = sent;
	notify(path, { event: "progress", key: h.key, rid: h.rid, sent, size });
	land(path);
}

// --- pull ----------------------------------------------------------------------

function answerUpload(path: Path, h: Handle, rid: unknown, state: string): void {
	notify(path, {
		event: "upload",
		key: h.key,
		rid,
		token: h.token,
		state,
		size: h.file.size,
		error: h.error,
	});
}

function pulled(path: Path, h: Handle, result: TransferResult): void {
	h.pull = null;
	const waiters = h.waiters;
	h.waiters = [];
	h.rid = null;
	if (result.error === "") {
		h.token = result.token;
		h.state = "landed";
		h.sent = h.file.size;
		h.error = "";
	} else {
		h.token = null;
		// A canceled pull leaves the file as it was picked; nothing is cached.
		h.state = result.error === "canceled" ? "picked" : "failed";
		h.sent = result.error === "canceled" ? 0 : h.sent;
		h.error = result.error;
	}
	const state = result.error === "canceled" ? "canceled" : h.state;
	for (const rid of waiters) answerUpload(path, h, rid, state);
	if (live(path, h)) land(path);
}

function startPull(path: Path, h: Handle, rid: unknown, url: string): void {
	h.state = "pulling";
	h.sent = 0;
	h.error = "";
	h.rid = typeof rid === "string" ? rid : null;
	h.waiters = [rid as string];
	h.reportedAt = Number.NEGATIVE_INFINITY;
	h.reported = 0;
	const transfer = postBlob(url, h.file, (sent) => progressed(path, h, sent));
	h.pull = transfer;
	void transfer.done.then((result) => pulled(path, h, result));
	land(path);
}

const pull: NodeHandler = (ctx, payload) => {
	const { key, rid, url } = fields(payload);
	const found = targets(ctx.path, key);
	if (found.length === 0) {
		ctx.send(OPS.notify, {
			event: "upload",
			key: key ?? null,
			rid,
			token: null,
			state: "failed",
			size: 0,
			error: "no_file",
		});
		return;
	}
	for (const h of found) {
		if (h.state === "landed" && h.token) answerUpload(ctx.path, h, rid, "landed");
		else if (h.state === "pulling") h.waiters.push(rid as string);
		else startPull(ctx.path, h, rid, str(url) ?? "");
	}
};

// --- slice -----------------------------------------------------------------------

const slice: NodeHandler = (ctx, payload) => {
	const { key, rid, url, start, end } = fields(payload);
	const path = ctx.path;
	const h = target(path, key);
	const answer = (extra: Fields) =>
		ctx.send(OPS.notify, { event: "slice", key: h?.key ?? key ?? null, rid, ...extra });
	if (!h) {
		answer({ token: null, cached: false, state: "failed", size: 0, error: "no_file" });
		return;
	}
	const size = h.file.size;
	const a = asIndex(start, size, 0);
	const b = Math.max(a, asIndex(end, size, size));
	if (h.state === "landed" && h.token) {
		answer({ token: h.token, cached: true, state: "landed", size: b - a, error: "" });
		return;
	}
	const transfer = postBlob(str(url) ?? "", h.file.slice(a, b));
	h.slices.add(transfer);
	void transfer.done.then((result) => {
		h.slices.delete(transfer);
		if (result.error === "unreadable" && live(path, h) && h.state !== "pulling") {
			// The file is gone from disk: say so in the value, the row strikes it.
			h.state = "failed";
			h.error = "unreadable";
			h.token = null;
			land(path);
		}
		answer({
			token: result.token,
			cached: false,
			state: result.error === "" ? "landed" : result.error === "canceled" ? "canceled" : "failed",
			size: result.error === "" ? result.size : b - a,
			error: result.error,
		});
	});
};

// --- cancel, discard, remove ----------------------------------------------------

const cancel: NodeHandler = (ctx, payload) => {
	for (const h of targets(ctx.path, fields(payload).key)) h.pull?.abort();
};

const discard: NodeHandler = (ctx, payload) => {
	const { key, rid } = fields(payload);
	const h = target(ctx.path, key);
	let token: string | null = null;
	if (h) {
		h.pull?.abort();
		token = h.token;
		h.token = null;
		h.sent = 0;
		if (h.state === "landed") h.state = "picked";
		land(ctx.path);
	}
	ctx.send(OPS.notify, { event: "discard", key: h?.key ?? key ?? null, rid, token });
};

const removeFileOp: NodeHandler = (ctx, payload) => {
	const h = target(ctx.path, fields(payload).key);
	if (!h) return;
	removeFile(ctx.path, h.key);
	land(ctx.path);
};

/** Put the node back to no files. Sends nothing: the program asked. */
const reset: NodeHandler = (ctx) => {
	dropFiles(ctx.path);
	resetInput(ctx.path);
};

/**
 * A write takes chrome (accept, prompt, max_size, label, ...) and never a
 * value: a program cannot put a file in a picker.
 */
const write: NodeHandler = (ctx, payload) => {
	if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;
	const { value: _ignored, ...chrome } = payload as Fields;
	ctx.update((props) => {
		Object.assign(props, chrome);
	});
};

export const uploadHandlers: Record<string, NodeHandler> = {
	write,
	reset,
	pull,
	slice,
	cancel,
	discard,
	remove_file: removeFileOp,
};
