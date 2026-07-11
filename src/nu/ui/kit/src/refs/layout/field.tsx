// FieldRef -- labelled form-field wrapper. Display-only chrome around
// exactly one child input Ref. One `write` op carries every chrome
// mutation (label, help, error, required); payload is a partial map.
// The single child is an absolute wire path passed via the mount
// `fields` list; the renderer resolves it through the global slice
// table and dispatches to its renderer. Wires aria-invalid /
// aria-describedby per a11y.md §5.

import { useId } from "react";
import { ErrorBoundary } from "../../components/ErrorBoundary";
import { Text } from "../../components/ui/text";
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
	const childPath = childPaths.length === 1 ? childPaths[0] : undefined;
	const childSlice = childPath ? refs[childPath] : null;
	const Comp = childSlice ? renderers[childSlice.type] : null;
	const helpId = useId();
	const errorId = useId();
	const showBottom = hasError || help.length > 0;
	const describedBy = hasError ? errorId : help ? helpId : undefined;

	return (
		<div className="flex flex-col gap-1">
			{label ? (
				<Text
					as="span"
					size="sm"
					tone={hasError ? "danger" : "secondary"}
					weight="medium"
				>
					{label}
					{required ? (
						<span className="text-accent ml-0.5" aria-hidden>
							*
						</span>
					) : null}
				</Text>
			) : null}
			<div aria-describedby={describedBy} aria-invalid={hasError || undefined}>
				{Comp && childPath && childSlice ? (
					<ErrorBoundary label={`${childPath} (${childSlice.type})`}>
						<Comp path={childPath} />
					</ErrorBoundary>
				) : (
					<Text size="xs" tone="danger" mono>
						no child at {childPath ?? "(unset)"}
					</Text>
				)}
			</div>
			{showBottom ? (
				<Text
					id={hasError ? errorId : helpId}
					as="span"
					size="xs"
					tone={hasError ? "danger" : "secondary"}
				>
					{hasError ? error : help}
				</Text>
			) : null}
		</div>
	);
}

export const FieldRef: RefEntry = { factory, component: FieldView };
