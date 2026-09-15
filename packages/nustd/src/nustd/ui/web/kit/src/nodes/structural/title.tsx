// TitleRef -- structural type bound to document.title.
// Index-level. Renders nothing into the body.
//
// Slot-level props:
//   default: initial title applied on mount before any host write.
//   suffix:  appended to every write (and to the default seed).
// The wire payload on `write` stays the raw host string; the suffix is
// applied only on the browser side.
//
// `write` is a handler because it has to touch document.title, which no
// amount of prop merging does. The mount-time seed used to live in the
// factory; there is no factory now, so it runs in an effect. The component
// renders null but still mounts, so the effect fires exactly once per node.
// Nothing is installed, so there is no teardown and no `dispose`.

import type { Props } from "@nustackdev/ui-core";
import { useEffect } from "react";
import { type NodeEntry, type NodeProps, nodeAt, pathKey, useProps, useSetValue } from "../../tree";

function _str(v: unknown): string {
	return typeof v === "string" ? v : "";
}

function _suffix(props: Props): string {
	return _str(props.suffix);
}

// Structural type: zero body output. The effect is the whole point of
// mounting it.
function TitleView({ path }: NodeProps) {
	const props = useProps(path);
	const initial = _str(props.default);
	const suffix = _suffix(props);
	const key = pathKey(path);
	const setValue = useSetValue(path);
	useEffect(() => {
		// Seed document.title once if we have a non-empty initial. Suffix-only
		// with an empty default is left alone to avoid a stray leading-suffix
		// title bar. A host write can land before this component mounts, and
		// that write wins: the seed is a default, not an override.
		if (initial === "") return;
		if (nodeAt(path)?.props.value !== undefined) return;
		document.title = initial + suffix;
		setValue(initial);
		// `key` is the path by value; `nodeAt` is read once, not subscribed.
	}, [initial, suffix, key, setValue]);
	return null;
}

export const TitleRef: NodeEntry = {
	component: TitleView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				const base = payload == null ? "" : String(payload);
				props.value = base;
				document.title = base + _suffix(props);
			}),
	},
};
