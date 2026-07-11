// TextRef -- display-only paragraph string. Renders via kit Text primitive.
//
// Server-owned. One `write` op carries a full string replace. Nil payload
// (Nu sentinel) maps to the empty string. Class-level default is seeded
// from the mount field `props.value` when non-empty. Wire strings often
// carry `\n`; we preserve whitespace at the render site.

import { Text } from "../../components/ui/text";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const factory: SliceFactory = (path, ctx, props) => ({
	type: "TextRef",
	value: typeof props?.value === "string" ? (props.value as string) : "",
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.value = v == null ? "" : String(v);
		}),
});

function TextView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	return (
		<Text as="p" size="base" tone="primary" className="whitespace-pre-wrap">
			{value}
		</Text>
	);
}

export const TextRef: RefEntry = { factory, component: TextView };
