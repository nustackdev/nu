// TitleRef -- structural Ref bound to document.title.
// Index-level. Not rendered into the body.

import type { RefEntry, SliceFactory } from "./types";

const factory: SliceFactory = (_path, _ctx) => ({
	type: "TitleRef",
	value: "",
	write: (v) => {
		const s = v == null ? "" : String(v);
		document.title = s;
	},
});

// Structural Ref: zero body output.
function TitleView(_: { path: string }) {
	return null;
}

export const TitleRef: RefEntry = { factory, component: TitleView };
