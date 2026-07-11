// Fieldset -- grouped fields with a legend and shared vertical spacing.
// Display-only, server-owned. One `write` op carries every chrome mutation
// (legend, gap, disabled); payload is a partial map. Children are absolute
// wire paths in the mount payload; the renderer resolves each through the
// global slice table and dispatches to its renderer. The `disabled` flag
// is visual-only -- we deliberately do not set the HTML `disabled`
// attribute on `<fieldset>` because that would cascade to child inputs.

import { ErrorBoundary } from "../../components/ErrorBoundary";
import { renderers } from "../../refs";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const GAP_CLASSES: Record<string, string> = {
	sm: "gap-2",
	md: "gap-4",
	lg: "gap-6",
};

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "Fieldset",
	value: null,
	legend: typeof props?.legend === "string" ? (props.legend as string) : "",
	gap: typeof props?.gap === "string" ? (props.gap as string) : "md",
	disabled: typeof props?.disabled === "boolean" ? (props.disabled as boolean) : false,
	children: Array.isArray(children) ? [...children] : [],
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as { legend?: unknown; gap?: unknown; disabled?: unknown };
			if ("legend" in p && p.legend != null) slice.legend = String(p.legend);
			if ("gap" in p && p.gap != null) slice.gap = String(p.gap);
			if ("disabled" in p && p.disabled != null) slice.disabled = Boolean(p.disabled);
		}),
});

function FieldsetView({ path }: { path: string }) {
	const legend = useStore((s) => (s.refs[path]?.legend as string) ?? "");
	const gap = useStore((s) => (s.refs[path]?.gap as string) ?? "md");
	const disabled = useStore((s) => (s.refs[path]?.disabled as boolean) ?? false);
	const childPaths = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);

	const gapCls = GAP_CLASSES[gap] ?? GAP_CLASSES.md;
	const rootCls = ["border border-border rounded-md p-4", disabled ? "opacity-50" : ""]
		.filter(Boolean)
		.join(" ");

	return (
		<fieldset className={rootCls}>
			{legend ? <legend className="text-sm font-semibold px-1">{legend}</legend> : null}
			<div className={`flex flex-col ${gapCls}`}>
				{childPaths.map((cp) => {
					const childSlice = refs[cp];
					if (!childSlice) {
						return (
							<div key={cp} className="text-xs text-destructive font-mono">
								no ref at {cp}
							</div>
						);
					}
					const Comp = renderers[childSlice.type];
					if (!Comp) {
						return (
							<div key={cp} className="text-xs text-destructive font-mono">
								no renderer for {childSlice.type}
							</div>
						);
					}
					return (
						<ErrorBoundary key={cp} label={`${cp} (${childSlice.type})`}>
							<Comp path={cp} />
						</ErrorBoundary>
					);
				})}
			</div>
		</fieldset>
	);
}

export const Fieldset: RefEntry = { factory, component: FieldsetView };
