// HeadingRef -- display-only heading with selectable level (h1..h4) and align.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. A bare string payload is
// accepted as a legacy shorthand for `{label: <string>}`. Class-level defaults
// come in on the mount field `props` and seed the slice.

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const LEVEL_CLASSES: Record<number, string> = {
	1: "text-3xl font-semibold mb-3",
	2: "text-2xl font-semibold mb-2",
	3: "text-xl font-medium mb-2",
	4: "text-lg font-medium mb-1",
};

const ALIGN_CLASSES: Record<string, string> = {
	left: "text-left",
	center: "text-center",
	right: "text-right",
};

function clampLevel(n: unknown): number {
	const v = Number(n);
	if (!Number.isInteger(v)) return 1;
	if (v < 1) return 1;
	if (v > 4) return 4;
	return v;
}

function normAlign(a: unknown): string {
	return typeof a === "string" && a in ALIGN_CLASSES ? a : "left";
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "HeadingRef",
	value: null,
	label: typeof props?.label === "string" ? (props.label as string) : "",
	level: clampLevel(props?.level ?? 1),
	align: normAlign(props?.align ?? "left"),
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			// Legacy shorthand: bare string maps to {label: ...}.
			if (typeof v === "string" || v == null) {
				slice.label = v == null ? "" : String(v);
				return;
			}
			const p = v as { label?: unknown; level?: unknown; align?: unknown };
			if ("label" in p) {
				slice.label = p.label == null ? "" : String(p.label);
			}
			if ("level" in p) {
				slice.level = p.level == null ? 1 : clampLevel(p.level);
			}
			if ("align" in p) {
				slice.align = p.align == null ? "left" : normAlign(p.align);
			}
		}),
});

function HeadingView({ path }: { path: string }) {
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const level = useStore((s) => (s.refs[path]?.level as number) ?? 1);
	const align = useStore((s) => (s.refs[path]?.align as string) ?? "left");
	const sizeCls = LEVEL_CLASSES[level] ?? LEVEL_CLASSES[1];
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.left;
	const cls = `${sizeCls} ${alignCls}`;
	switch (level) {
		case 2:
			return <h2 className={cls}>{label}</h2>;
		case 3:
			return <h3 className={cls}>{label}</h3>;
		case 4:
			return <h4 className={cls}>{label}</h4>;
		default:
			return <h1 className={cls}>{label}</h1>;
	}
}

export const HeadingRef: RefEntry = { factory, component: HeadingView };
