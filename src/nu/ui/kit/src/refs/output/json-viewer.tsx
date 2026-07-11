// JsonViewerRef -- display-only collapsible json tree.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map over the config keys (value, expand_depth, theme, copyable, sortable,
// max_height). Missing keys leave the slice untouched. Class-level defaults
// come in on the mount field `props` and seed the slice. Composes the kit
// JsonView primitive (which threads palette tokens through the underlying
// library) plus a ghost IconButton for copy.

import { Copy } from "lucide-react";
import { IconButton } from "../../components/ui/icon-button";
import { JsonView } from "../../components/ui/json-view";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

function sortKeys(v: unknown): unknown {
	if (Array.isArray(v)) return v.map(sortKeys);
	if (v && typeof v === "object") {
		const src = v as Record<string, unknown>;
		const out: Record<string, unknown> = {};
		for (const k of Object.keys(src).sort()) out[k] = sortKeys(src[k]);
		return out;
	}
	return v;
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "JsonViewerRef",
	value: props?.value ?? null,
	expand_depth: typeof props?.expand_depth === "number" ? (props.expand_depth as number) : 2,
	theme: typeof props?.theme === "string" ? (props.theme as string) : "light",
	copyable: typeof props?.copyable === "boolean" ? (props.copyable as boolean) : true,
	sortable: typeof props?.sortable === "boolean" ? (props.sortable as boolean) : false,
	max_height: typeof props?.max_height === "number" ? (props.max_height as number) : null,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as Record<string, unknown>;
			if ("value" in p) slice.value = p.value ?? null;
			if ("expand_depth" in p)
				slice.expand_depth = p.expand_depth == null ? 2 : Number(p.expand_depth);
			if ("theme" in p) slice.theme = p.theme == null ? "light" : String(p.theme);
			if ("copyable" in p) slice.copyable = p.copyable == null ? true : Boolean(p.copyable);
			if ("sortable" in p) slice.sortable = p.sortable == null ? false : Boolean(p.sortable);
			if ("max_height" in p) slice.max_height = p.max_height == null ? null : Number(p.max_height);
		}),
});

function JsonViewerView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value);
	const depth = useStore((s) => (s.refs[path]?.expand_depth as number) ?? 2);
	const copyable = useStore((s) => (s.refs[path]?.copyable as boolean) ?? true);
	const sortable = useStore((s) => (s.refs[path]?.sortable as boolean) ?? false);
	const maxH = useStore((s) => (s.refs[path]?.max_height as number | null) ?? null);
	const data = sortable ? sortKeys(value ?? {}) : (value ?? {});
	const copy = () => {
		if (navigator.clipboard?.writeText) {
			void navigator.clipboard.writeText(JSON.stringify(value, null, 2));
		}
	};
	return (
		<div
			className="rounded-md border border-border-default bg-bg-surface"
			style={{ maxHeight: maxH ?? undefined, overflow: maxH ? "auto" : undefined }}
		>
			{copyable && (
				<div className="flex justify-end p-1">
					<IconButton variant="ghost" size="sm" aria-label="copy" onClick={copy}>
						<Copy />
					</IconButton>
				</div>
			)}
			<div className="px-3 pb-2">
				<JsonView value={data} collapsed={depth} />
			</div>
		</div>
	);
}

export const JsonViewerRef: RefEntry = { factory, component: JsonViewerView };
