// NavRef -- structural type bound to the page's location.
//
// write(payload): four shapes ride on the same op.
//   - bare string "/feed"                            -> push
//   - {action: "push",    uri: "/feed"}              -> push
//   - {action: "replace", uri: "/feed"}              -> replace
//   - {action: "back"}                               -> back
//   - {action: "forward"}                            -> forward
//
// Every move goes through the active navigator (../../tree/navigate), plain
// browser history unless the host installed its own router. So a server
// write moves whatever the host draws, not just the address bar.
//
// The current URI is mirrored into `value` so renderers can subscribe
// normally (the body looks up the active page by uri and picks the matching
// subtree).
//
// Three pieces of behaviour, none of which a prop merge can stand in for:
//   - `write` drives the navigator, so it is a handler. It has to work
//     whether or not anything is mounted.
//   - the component follows the page's location in an effect (the one
//     source NavItem reads too, `subscribeLocation`: back and forward with
//     plain history, a plain pushState, any route move under a host router),
//     mirrors the new uri and notifies the server. A move this ref's own
//     write made is mirrored but not notified: the server asked for it.
//   - `read` answers with the live URI, since the page can move outside
//     anything this node saw.

import { OPS } from "@nustackdev/ui-core";
import { useEffect } from "react";
import {
	activeNavigator,
	type NodeEntry,
	type NodeProps,
	nodeAt,
	pathKey,
	subscribeLocation,
	useSend,
	useSetValue,
} from "../../tree";

type WriteAction = "push" | "replace" | "back" | "forward";
type WritePayload = string | null | { action?: WriteAction; uri?: string | null };

function toUri(raw: unknown): string {
	return raw == null ? "/" : String(raw);
}

// Set while a write moves the page, so the move it causes is not echoed back
// as a notify. A synchronous navigator moves inside the window; back and
// forward land later, as a popstate, and are notified like a user's.
let writing = false;

function moved(go: () => void): void {
	writing = true;
	try {
		go();
	} finally {
		writing = false;
	}
}

// Structural type: zero body output. The effect is the whole point of
// mounting it.
function NavView({ path }: NodeProps) {
	const setValue = useSetValue(path);
	const send = useSend(path);
	const key = pathKey(path);
	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by its key.
	useEffect(() => {
		const nav = activeNavigator();
		// Mirror where the page actually is. A write that landed before this
		// mounted already moved it, so the live uri is what it mirrored.
		setValue(nav.current());
		const onMove = () => {
			const uri = activeNavigator().current();
			// Most of what the location source reports is no move (a tree
			// change, a host router's focus change): only a new uri is one,
			// and only while this node is still there to mirror it.
			const node = nodeAt(path);
			if (!node || uri === node.props.value) return;
			setValue(uri);
			if (!writing) send(OPS.notify, uri);
		};
		return subscribeLocation(onMove);
		// `key` is the path by value: a node moving means a fresh listener.
	}, [key, setValue, send]);
	return null;
}

export const NavRef: NodeEntry = {
	component: NavView,
	handlers: {
		write: (ctx, payload) => {
			const nav = activeNavigator();
			const mirror = () =>
				ctx.update((props) => {
					props.value = activeNavigator().current();
				});
			const p = payload as WritePayload;
			const action = p == null || typeof p === "string" ? "push" : (p.action ?? "push");
			const uri = p == null || typeof p === "string" ? toUri(p) : toUri(p.uri);
			if (action === "push") {
				moved(() => nav.push(uri));
				mirror();
				return;
			}
			if (action === "replace") {
				moved(() => nav.replace(uri));
				mirror();
				return;
			}
			if (action === "back") {
				// The move lands later; its subscriber mirrors and notifies.
				nav.back();
				return;
			}
			if (action === "forward") {
				nav.forward();
				return;
			}
			console.warn(`nudle NavRef: unknown write action "${String(action)}"`);
		},
		read: (ctx) => {
			ctx.send(OPS.read, activeNavigator().current(), ctx.frame.id);
		},
	},
};
