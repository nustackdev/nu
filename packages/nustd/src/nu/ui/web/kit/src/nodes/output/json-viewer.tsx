// JsonViewerRef -- display-only collapsible json tree.
//
// Server-owned. A write is a partial merge over the config keys (value,
// expand_depth, theme, copyable, sortable, max_height) into the node's props,
// which is the default store behaviour, so there is no handler. Nil on any
// key reads back as the class default at render time. Composes the kit
// JsonView primitive (which threads palette tokens through the underlying
// library) plus a ghost IconButton for copy.

import { Copy } from "lucide-react";
import { IconButton } from "../../components/ui/icon-button";
import { JsonView } from "../../components/ui/json-view";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useNumberProp,
	useProp,
	useValue,
} from "../../tree";

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

function JsonViewerView({ path }: NodeProps) {
	const value = useValue<unknown>(path, null);
	const depth = useNumberProp(path, "expand_depth", 2);
	const copyable = useBoolProp(path, "copyable", true);
	const sortable = useBoolProp(path, "sortable");
	const rawMaxH = useProp<unknown>(path, "max_height", null);
	const maxH = typeof rawMaxH === "number" && Number.isFinite(rawMaxH) ? rawMaxH : null;
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

export const JsonViewerRef: NodeEntry = { component: JsonViewerView };
