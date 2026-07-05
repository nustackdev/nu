// FieldRef -- labelled form-field wrapper. Display-only chrome around
// exactly one child input Ref. One `write` op carries every chrome
// mutation (label, help, error, required); payload is a partial map.
// The single child is an absolute wire path passed via the mount
// `fields` list; the renderer resolves it through the global slice
// table and dispatches to its renderer.

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { renderers } from "../../refs";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "FieldRef",
	value: null,
	label: typeof props?.label === "string" ? (props.label as string) : "",
	help: typeof props?.help === "string" ? (props.help as string) : "",
	error: typeof props?.error === "string" ? (props.error as string) : "",
	required: typeof props?.required === "boolean" ? (props.required as boolean) : false,
	children: Array.isArray(children) ? [...children] : [],
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				label?: unknown;
				help?: unknown;
				error?: unknown;
				required?: unknown;
			};
			// Nil for a string field lands as "". Nil for required lands as false.
			if ("label" in p) slice.label = p.label == null ? "" : String(p.label);
			if ("help" in p) slice.help = p.help == null ? "" : String(p.help);
			if ("error" in p) slice.error = p.error == null ? "" : String(p.error);
			if ("required" in p) slice.required = p.required == null ? false : Boolean(p.required);
		}),
});

function FieldView({ path }: { path: string }) {
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const help = useStore((s) => (s.refs[path]?.help as string) ?? "");
	const error = useStore((s) => (s.refs[path]?.error as string) ?? "");
	const required = useStore((s) => Boolean(s.refs[path]?.required));
	const childPaths = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);

	const hasError = error.length > 0;
	const tint = hasError ? "text-destructive" : "text-muted-foreground";
	const childPath = childPaths.length === 1 ? childPaths[0] : undefined;
	const childSlice = childPath ? refs[childPath] : null;
	const Comp = childSlice ? renderers[childSlice.type] : null;
	const showBottom = hasError || help.length > 0;

	return (
		// biome-ignore lint/a11y/noLabelWithoutControl: child Ref renders the actual input.
		<label className="flex flex-col gap-1">
			{label ? (
				<span className={`text-sm font-medium ${hasError ? "text-destructive" : ""}`}>
					{label}
					{required ? <span className="text-destructive ml-0.5">*</span> : null}
				</span>
			) : null}
			{Comp && childPath && childSlice ? (
				<ErrorBoundary label={`${childPath} (${childSlice.type})`}>
					<Comp path={childPath} />
				</ErrorBoundary>
			) : (
				<div className="text-xs text-destructive font-mono">
					no child at {childPath ?? "(unset)"}
				</div>
			)}
			{showBottom ? <span className={`text-xs ${tint}`}>{hasError ? error : help}</span> : null}
		</label>
	);
}

export const FieldRef: RefEntry = { factory, component: FieldView };
