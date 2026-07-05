// NavRef -- structural Ref bound to window.history + window.location.
//
// write(payload): four shapes ride on the same op.
//   - bare string "/feed"                            -> push
//   - {action: "push",    uri: "/feed"}              -> pushState
//   - {action: "replace", uri: "/feed"}              -> replaceState
//   - {action: "back"}                               -> history.back()
//   - {action: "forward"}                            -> history.forward()
//
// popstate (user back/forward) or link clicks that bubble through the
// renderer dispatch into this slice. `get` returns the current URI when
// the server issues a read.
//
// We mirror the current URI into the store as `value` so renderers can
// subscribe normally (the body looks up the active page by uri and picks
// the matching subtree). On mount we seed `value` from window.location
// and install a popstate listener. The listener emits a `notify` to the
// server with the new URI as payload. dispose removes the listener.

import { OP_NOTIFY } from "../../protocol";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

function currentUri(): string {
	return window.location.pathname + window.location.search + window.location.hash;
}

type WriteAction = "push" | "replace" | "back" | "forward";
type WritePayload = string | null | { action?: WriteAction; uri?: string | null };

function toUri(raw: unknown): string {
	return raw == null ? "/" : String(raw);
}

const factory: SliceFactory = (path, ctx) => {
	const initial = currentUri();

	// popstate fires on back/forward navigation (user or programmatic).
	// Update the local store and notify the server.
	const onPopState = () => {
		const uri = currentUri();
		ctx.set((refs) => {
			if (refs[path]) refs[path].value = uri;
		});
		ctx.send({ op: OP_NOTIFY, ref: path, payload: uri });
	};
	window.addEventListener("popstate", onPopState);

	const pushUri = (uri: string) => {
		// Avoid duplicate history entries for the same URI.
		if (uri !== currentUri()) {
			window.history.pushState({}, "", uri);
		}
		ctx.set((refs) => {
			if (refs[path]) refs[path].value = uri;
		});
	};

	const replaceUri = (uri: string) => {
		if (uri !== currentUri()) {
			window.history.replaceState({}, "", uri);
		}
		ctx.set((refs) => {
			if (refs[path]) refs[path].value = uri;
		});
	};

	return {
		type: "NavRef",
		value: initial,
		write: (v) => {
			const payload = v as WritePayload;
			if (payload == null || typeof payload === "string") {
				pushUri(toUri(payload));
				return;
			}
			const action = payload.action ?? "push";
			if (action === "push") {
				pushUri(toUri(payload.uri));
				return;
			}
			if (action === "replace") {
				replaceUri(toUri(payload.uri));
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
		get: () => useStore.getState().refs[path]?.value ?? currentUri(),
		dispose: () => window.removeEventListener("popstate", onPopState),
	};
};

// Structural Ref: zero body output.
function NavView(_: { path: string }) {
	return null;
}

export const NavRef: RefEntry = { factory, component: NavView };
