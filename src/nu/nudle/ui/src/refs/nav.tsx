// NavRef -- structural Ref bound to window.history + window.location.
//
// write(uri): pushes a new entry onto history (host-driven navigation).
// popstate (user back/forward) or link clicks that bubble through the
// renderer dispatch into this slice. `get` returns the current URI when
// the server issues a read.
//
// We mirror the current URI into the store as `value` so renderers can
// subscribe normally (the body looks up the active page by uri and picks
// the matching subtree). On mount we seed `value` from window.location
// and install a popstate listener. The listener emits a `notify` to the
// server with the new URI as payload.

import { OP_NOTIFY } from "../protocol";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

function currentUri(): string {
	return window.location.pathname + window.location.search + window.location.hash;
}

const factory: SliceFactory = (path, ctx) => {
	// Initial value: whatever URI the browser is at right now.
	const initial = currentUri();

	// popstate fires on back/forward navigation. Update the local store
	// and notify the server.
	const onPopState = () => {
		const uri = currentUri();
		ctx.set((refs) => {
			if (refs[path]) refs[path].value = uri;
		});
		ctx.send({ op: OP_NOTIFY, ref: path, payload: uri });
	};
	window.addEventListener("popstate", onPopState);

	return {
		type: "NavRef",
		value: initial,
		write: (v) => {
			const uri = v == null ? "/" : String(v);
			// Avoid duplicate history entries for the same URI.
			if (uri !== currentUri()) {
				window.history.pushState({}, "", uri);
			}
			ctx.set((refs) => {
				if (refs[path]) refs[path].value = uri;
			});
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
