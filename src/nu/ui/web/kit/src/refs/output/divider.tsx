// DividerRef -- display-only horizontal rule with optional inline label.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. Class-level defaults
// come in on the mount field `props` and seed the slice. Composes the kit
// Separator primitive, which owns the labeled layout when `label` is set.
//
// TODO(retune): Separator primitive centers the label; `align` (left/right)
// asymmetric side widths from the old Ref are not yet supported by the
// primitive. Left as-is until the primitive grows an align slot.

import { Separator } from "../../components/ui/separator";
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
	return (
		<div className="my-4 w-full">
			<Separator label={label || undefined} />
		</div>
	);
}

export const DividerRef: RefEntry = { factory, component: DividerView };
