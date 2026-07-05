// JsonViewerRef -- display-only collapsible json tree.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map over the config keys (value, expand_depth, theme, copyable, sortable,
// max_height). Missing keys leave the slice untouched. Class-level defaults
// come in on the mount field `props` and seed the slice.

import JsonView from "@uiw/react-json-view";
import { darkTheme } from "@uiw/react-json-view/dark";
import { lightTheme } from "@uiw/react-json-view/light";
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

function CopyButton({ text }: { text: string }) {
	return (
		<button
			type="button"
			className="rounded border border-gray-300 px-2 py-0.5 text-xs text-gray-600 hover:bg-gray-50"
			onClick={() => {
				void navigator.clipboard?.writeText(text);
			}}
		>
			copy
		</button>
	);
}

function JsonViewerView({ path }: { path: string }) {
	const value = useStore((s) => s.refs[path]?.value);
	const depth = useStore((s) => (s.refs[path]?.expand_depth as number) ?? 2);
	const theme = useStore((s) => (s.refs[path]?.theme as string) ?? "light");
	const copyable = useStore((s) => (s.refs[path]?.copyable as boolean) ?? true);
	const sortable = useStore((s) => (s.refs[path]?.sortable as boolean) ?? false);
	const maxH = useStore((s) => (s.refs[path]?.max_height as number | null) ?? null);
	const data = sortable ? sortKeys(value ?? {}) : (value ?? {});
	const wrapperStyle: React.CSSProperties = {
		maxHeight: maxH ?? undefined,
		overflow: maxH ? "auto" : undefined,
		padding: "8px 12px",
		borderRadius: 6,
		border: "1px solid #e5e7eb",
	};
	return (
		<div className="space-y-2">
			{copyable && (
				<div className="flex justify-end">
					<CopyButton text={JSON.stringify(value, null, 2)} />
				</div>
			)}
			<div style={wrapperStyle}>
				<JsonView
					value={data as object}
					collapsed={depth}
					displayDataTypes={false}
					displayObjectSize={true}
					enableClipboard={false}
					style={theme === "dark" ? darkTheme : lightTheme}
				/>
			</div>
		</div>
	);
}

export const JsonViewerRef: RefEntry = { factory, component: JsonViewerView };
