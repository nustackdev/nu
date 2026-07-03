// MarkdownRef -- display-only markdown source, rendered as commonmark.
//
// Server-owned. One `write` op carries a full string replace. Nil payload
// (Nu sentinel) maps to the empty string. Class-level default is seeded
// from the mount field `props.value` when non-empty. No raw html passthrough:
// react-markdown runs without rehype-raw so any <...> in the source renders
// as literal text.

import ReactMarkdown from "react-markdown";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const factory: SliceFactory = (path, ctx, props) => ({
	type: "MarkdownRef",
	value: typeof props?.value === "string" ? (props.value as string) : "",
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.value = v == null ? "" : String(v);
		}),
});

function MarkdownView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	return (
		<div className="prose prose-sm max-w-none">
			<ReactMarkdown>{value}</ReactMarkdown>
		</div>
	);
}

export const MarkdownRef: RefEntry = { factory, component: MarkdownView };
