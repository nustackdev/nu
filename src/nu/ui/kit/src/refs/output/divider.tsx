// DividerRef -- display-only horizontal rule with optional inline label.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. Class-level defaults
// come in on the mount field `props` and seed the slice.

import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const ALIGN_VALUES = new Set(["left", "center", "right"]);

function normAlign(a: unknown): string {
	return typeof a === "string" && ALIGN_VALUES.has(a) ? a : "center";
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "DividerRef",
	value: null,
	label: typeof props?.label === "string" ? (props.label as string) : "",
	align: normAlign(props?.align ?? "center"),
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			if (v == null || typeof v !== "object") return;
			const p = v as { label?: unknown; align?: unknown };
			if ("label" in p) {
				slice.label = p.label == null ? "" : String(p.label);
			}
			if ("align" in p) {
				slice.align = p.align == null ? "center" : normAlign(p.align);
			}
		}),
});

function DividerView({ path }: { path: string }) {
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const align = useStore((s) => (s.refs[path]?.align as string) ?? "center");
	if (label === "") {
		return <hr className="my-4 border-t border-border" />;
	}
	let leftGrowCls = "flex-1";
	let rightGrowCls = "flex-1";
	if (align === "left") {
		leftGrowCls = "w-4 flex-none";
		rightGrowCls = "flex-1";
	} else if (align === "right") {
		leftGrowCls = "flex-1";
		rightGrowCls = "w-4 flex-none";
	}
	return (
		<div className="my-4 flex items-center gap-3 text-sm text-muted-foreground">
			<span className={`h-px bg-border ${leftGrowCls}`} />
			<span>{label}</span>
			<span className={`h-px bg-border ${rightGrowCls}`} />
		</div>
	);
}

export const DividerRef: RefEntry = { factory, component: DividerView };
