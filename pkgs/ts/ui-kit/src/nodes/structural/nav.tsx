// NavRef -- structural type bound to window.history + window.location.
//
// write(payload): four shapes ride on the same op.
//   - bare string "/feed"                            -> push
//   - {action: "push",    uri: "/feed"}              -> pushState
//   - {action: "replace", uri: "/feed"}              -> replaceState
//   - {action: "back"}                               -> history.back()
//   - {action: "forward"}                            -> history.forward()
//
// The current URI is mirrored into `value` so renderers can subscribe
// normally (the body looks up the active page by uri and picks the matching
// subtree).
//
// Three pieces of behaviour, none of which a prop merge can stand in for:
//   - `write` drives window.history, so it is a handler. It has to work
//     whether or not anything is mounted.
//   - the popstate listener (user back/forward) used to be installed by the
//     factory; there is no factory now, so the component installs it in an
//     effect and the effect cleanup removes it. The component renders null
//     but still mounts, so that is one listener per node, torn down with it.
//   - `read` answers with the live URI when we have nothing mirrored, since
//     the user can navigate outside anything we saw.

import { OPS } from "@nustackdev/ui-core";
import { useEffect } from "react";
import { type NodeEntry, type NodeProps, pathKey, useSend, useSetValue } from "../../tree";

function currentUri(): string {
	return window.location.pathname + window.location.search + window.location.hash;
}

type WriteAction = "push" | "replace" | "back" | "forward";
type WritePayload = string | null | { action?: WriteAction; uri?: string | null };

function toUri(raw: unknown): string {
	return raw == null ? "/" : String(raw);
}

// Structural type: zero body output. The effect is the whole point of
// mounting it.
function NavView({ path }: NodeProps) {
	const setValue = useSetValue(path);
	const send = useSend(path);
	const key = pathKey(path);
	useEffect(() => {
		// Mirror where the browser actually is. A write that landed before
		// this mounted already pushed its uri onto history, so location is
		// the same thing that write mirrored.
		setValue(currentUri());
		// popstate fires on back/forward navigation (user or programmatic).
		// Update the local value and notify the server.
		const onPopState = () => {
			const uri = currentUri();
			setValue(uri);
			send(OPS.notify, uri);
		};
		window.addEventListener("popstate", onPopState);
		return () => window.removeEventListener("popstate", onPopState);
		// `key` is the path by value: a node moving means a fresh listener.
	}, [key, setValue, send]);
	return null;
}

export const NavRef: NodeEntry = {
	component: NavView,
	handlers: {
		write: (ctx, payload) => {
			const mirror = (uri: string) =>
				ctx.update((props) => {
					props.value = uri;
				});
			const pushUri = (uri: string) => {
				// Avoid duplicate history entries for the same URI.
				if (uri !== currentUri()) window.history.pushState({}, "", uri);
				mirror(uri);
			};
			const replaceUri = (uri: string) => {
				if (uri !== currentUri()) window.history.replaceState({}, "", uri);
				mirror(uri);
			};
			const p = payload as WritePayload;
			if (p == null || typeof p === "string") {
				pushUri(toUri(p));
				return;
			}
			const action = p.action ?? "push";
			if (action === "push") {
				pushUri(toUri(p.uri));
				return;
			}
			if (action === "replace") {
				replaceUri(toUri(p.uri));
				return;
			}
			if (action === "back") {
				// popstate (if any) will mirror + notify; we do not pre-seed.
				window.history.back();
				return;
			}
			if (action === "forward") {
				window.history.forward();
				return;
			}
			console.warn(`nudle NavRef: unknown write action "${String(action)}"`);
		},
		read: (ctx) => {
			const mirrored = ctx.node.props.value;
			const uri = mirrored == null ? currentUri() : String(mirrored);
			ctx.send(OPS.read, uri, ctx.frame.id);
		},
	},
};
