// TitleRef -- structural Ref bound to document.title.
// Index-level. Not rendered into the body.
//
// Class-level defaults arrive via mount field `props`:
//   default: initial title applied on mount before any host write.
//   suffix:  appended to every write (and to the default seed).
// The wire payload on `write` stays the raw host string; the suffix
// is applied only on the browser side.

import type { RefEntry, RefSlice, SliceFactory } from "../types";

const factory: SliceFactory = (_path, _ctx, props) => {
	const initial = typeof props?.default === "string" ? (props.default as string) : "";
	const suffix = typeof props?.suffix === "string" ? (props.suffix as string) : "";

	const apply = (base: string) => {
		document.title = base + suffix;
	};

	// Seed document.title once if we have a non-empty initial. Suffix-only
	// with an empty default is left alone to avoid a stray leading-suffix
	// title bar.
	if (initial !== "") {
		apply(initial);
	}

	const slice: RefSlice = {
		type: "TitleRef",
		value: initial,
		suffix,
		write: (v) => {
			const base = v == null ? "" : String(v);
			slice.value = base;
			apply(base);
		},
		// No listeners installed today. Reserved as the detach point for
		// any future observer on document.title.
		dispose: () => {},
	};
	return slice;
};

// Structural Ref: zero body output.
function TitleView(_: { path: string }) {
	return null;
}

export const TitleRef: RefEntry = { factory, component: TitleView };
