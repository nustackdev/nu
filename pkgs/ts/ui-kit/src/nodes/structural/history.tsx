// HistoryRef -- the server's handle on the page's History (../../tree/history).
// `NavRef` is the same type under its old name, so a program built before
// the rename still draws.
//
// write(payload): every shape rides on the one op.
//   - bare string "/feed"                                  -> push
//   - {action: "push",    uri: "/feed", state?: {...}}     -> push
//   - {action: "replace", uri: "/feed", state?: {...}}     -> replace
//   - {action: "back"} / {action: "forward"}               -> back / forward
//   - {action: "set_query", query: {q: "x", page: null}}   -> replace with the
//     current query merged with that one (a null drops a key), the path,
//     hash and state kept. A replace, so a filter typed into never floods
//     back.
// A push or replace with no `state` leaves none.
//
// Reporting, one rule: every move the page makes reaches the server as a
// notify whose payload is the new uri (path, query and hash), except a move
// this ref's own write caused, whichever of the ops above it was. The server
// asked for that one. A move another HistoryRef made, the user's back button,
// a link the AnchorCatcher routed: all reported. The current uri is mirrored
// into `value` on every move, so a renderer can follow it like any prop.
//
// `read` answers with the whole entry, {uri, path, query, hash, state}, live:
// the page can move outside anything this node saw. The Python ref reads the
// uri off it, and the entry, the query and the state too.
//
// The writes work whether or not the node is mounted; the reporting needs it
// mounted, since it is an effect. Structural: it draws nothing.

import { OPS } from "@nustackdev/ui-core";
import { useEffect } from "react";
import {
	type Entry,
	History,
	mergeQuery,
	type NodeEntry,
	type NodeProps,
	nodeAt,
	pathKey,
	serializeQuery,
	useSend,
	useSetValue,
} from "../../tree";

type WriteAction = "push" | "replace" | "back" | "forward" | "set_query";
type WritePayload =
	| string
	| null
	| {
			action?: WriteAction;
			uri?: string | null;
			state?: unknown;
			query?: Record<string, unknown> | null;
	  };

/** The tag this ref's own moves carry, so it can tell them from the rest. */
function originOf(key: string): string {
	return `HistoryRef:${key}`;
}

function toUri(raw: unknown): string {
	return raw == null ? "/" : String(raw);
}

/** What `read` answers: the entry, with the uri under its wire name. */
export function entryPayload(entry: Entry): Record<string, unknown> {
	return {
		uri: entry.url,
		path: entry.path,
		query: entry.query,
		hash: entry.hash,
		state: entry.state,
	};
}

/** The current entry's url with `patch` merged into its query. */
function withQuery(entry: Entry, patch: Record<string, unknown>): string {
	const search = serializeQuery(mergeQuery(entry.query, patch));
	return entry.path + (search ? `?${search}` : "") + entry.hash;
}

function HistoryView({ path }: NodeProps) {
	const setValue = useSetValue(path);
	const send = useSend(path);
	const key = pathKey(path);
	useEffect(() => {
		const own = originOf(key);
		// Mirror where the page is. A write that landed before this mounted
		// already moved it, so the live uri is what it mirrors.
		setValue(History.current().url);
		return History.subscribe((move) => {
			// Only while this node is still there to mirror it.
			if (!nodeAt(path)) return;
			setValue(move.entry.url);
			if (move.origin !== own) send(OPS.notify, move.entry.url);
		});
		// `key` is the path by value: a node moving means a fresh listener.
	}, [key, setValue, send]);
	return null;
}

export const HistoryRef: NodeEntry = {
	component: HistoryView,
	handlers: {
		write: (ctx, payload) => {
			const opts = { origin: originOf(pathKey(ctx.path)) };
			const mirror = () =>
				ctx.update((props) => {
					props.value = History.current().url;
				});
			const p = payload as WritePayload;
			if (p == null || typeof p === "string") {
				History.push(toUri(p), undefined, opts);
				mirror();
				return;
			}
			const action = p.action ?? "push";
			if (action === "push" || action === "replace") {
				History[action](toUri(p.uri), p.state ?? undefined, opts);
				mirror();
				return;
			}
			if (action === "set_query") {
				const entry = History.current();
				History.replace(withQuery(entry, p.query ?? {}), entry.state, opts);
				mirror();
				return;
			}
			if (action === "back" || action === "forward") {
				// The move lands later, as a popstate, still tagged as ours.
				History[action](opts);
				return;
			}
			console.warn(`HistoryRef: unknown write action "${String(action)}"`);
		},
		read: (ctx) => {
			ctx.send(OPS.read, entryPayload(History.current()), ctx.frame.id);
		},
	},
};

/** The old name, kept so programs built before the rename still draw. */
export const NavRef: NodeEntry = HistoryRef;
