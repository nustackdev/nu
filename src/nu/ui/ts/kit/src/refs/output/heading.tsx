// HeadingRef -- display-only heading with selectable level (h1..h4) and align.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. A bare string payload is
// accepted as a legacy shorthand for `{label: <string>}`. Class-level defaults
// come in on the mount field `props` and seed the slice. Composes the kit
// Heading primitive: level maps to size, align to text-align utility.

import { Heading } from "../../components/ui/heading";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

// Match level to typography ladder from primitives.md §Heading.
const LEVEL_SIZES = {
	1: "3xl",
	2: "2xl",
	3: "xl",
	4: "lg",
} as const;

const ALIGN_CLASSES: Record<string, string> = {
	left: "text-left",
	center: "text-center",
	right: "text-right",
};

function clampLevel(n: unknown): 1 | 2 | 3 | 4 {
	const v = Number(n);
	if (!Number.isInteger(v)) return 1;
	if (v < 1) return 1;
	if (v > 4) return 4;
	return v as 1 | 2 | 3 | 4;
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
	const level = useStore((s) => (s.refs[path]?.level as 1 | 2 | 3 | 4) ?? 1);
	const align = useStore((s) => (s.refs[path]?.align as string) ?? "left");
	const size = LEVEL_SIZES[level] ?? LEVEL_SIZES[1];
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.left;
	const as = `h${level}` as "h1" | "h2" | "h3" | "h4";
	return (
		<Heading as={as} size={size} className={alignCls}>
			{label}
		</Heading>
	);
}

export const HeadingRef: RefEntry = { factory, component: HeadingView };
