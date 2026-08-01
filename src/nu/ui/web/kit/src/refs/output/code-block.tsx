// CodeBlockRef -- display-only preformatted code block with optional language label.
//
// Server-owned. One `write` op carries a partial dict of {code, language,
// show_copy}; missing keys leave slice fields alone. Nil on `code` /
// `language` coerces to ""; nil on `show_copy` falls back to the class
// default (true). No syntax highlighting in v1: the language label is
// informational only. Composes the kit Code primitive in block mode; the
// primitive owns the copy affordance when `copyable` is set.

import { Code } from "../../components/ui/code";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const DEFAULTS = {
	code: "",
	language: "",
	show_copy: true,
};

const factory: SliceFactory = (path, ctx, props) => ({
	type: "CodeBlockRef",
	value: null,
	code: typeof props?.code === "string" ? (props.code as string) : DEFAULTS.code,
	language: typeof props?.language === "string" ? (props.language as string) : DEFAULTS.language,
	show_copy:
		typeof props?.show_copy === "boolean" ? (props.show_copy as boolean) : DEFAULTS.show_copy,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as Record<string, unknown>;
			if ("code" in p) {
				slice.code = p.code == null ? "" : String(p.code);
			}
			if ("language" in p) {
				slice.language = p.language == null ? "" : String(p.language);
			}
			if ("show_copy" in p) {
				slice.show_copy = p.show_copy == null ? DEFAULTS.show_copy : Boolean(p.show_copy);
			}
		}),
});

function CodeBlockView({ path }: { path: string }) {
	const code = useStore((s) => (s.refs[path]?.code as string) ?? "");
	const language = useStore((s) => (s.refs[path]?.language as string) ?? "");
	const showCopy = useStore((s) => (s.refs[path]?.show_copy as boolean) ?? true);
	return (
		<Code block copyable={showCopy} language={language || undefined}>
			{code}
		</Code>
	);
}

export const CodeBlockRef: RefEntry = { factory, component: CodeBlockView };
