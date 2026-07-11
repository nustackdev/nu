// CodeBlockRef -- display-only preformatted code block with optional language label.
//
// Server-owned. One `write` op carries a partial dict of {code, language,
// show_copy}; missing keys leave slice fields alone. Nil on `code` /
// `language` coerces to ""; nil on `show_copy` falls back to the class
// default (true). No syntax highlighting in v1: the language label is
// informational only. The copy button is a browser-only affordance and
// does not emit a frame.

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
	const copy = () => {
		if (navigator.clipboard?.writeText) {
			navigator.clipboard.writeText(code).catch(() => {});
		}
	};
	const showHeader = language !== "" || showCopy;
	return (
		<div className="rounded border bg-muted">
			{showHeader && (
				<div className="flex items-center justify-between px-3 py-1 text-xs text-muted-foreground">
					<span>{language}</span>
					{showCopy && (
						<button type="button" onClick={copy} className="hover:text-foreground">
							copy
						</button>
					)}
				</div>
			)}
			<pre className="overflow-x-auto p-3 text-sm">
				<code className="font-mono whitespace-pre">{code}</code>
			</pre>
		</div>
	);
}

export const CodeBlockRef: RefEntry = { factory, component: CodeBlockView };
