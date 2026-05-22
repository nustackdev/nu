// BadgeRef -- display-only label with a variant tag.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. Class-level defaults
// come in on the mount field `props` and seed the slice.

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const VARIANT_CLASSES: Record<string, string> = {
	info: "bg-blue-100 text-blue-800",
	warn: "bg-yellow-100 text-yellow-800",
	ok: "bg-green-100 text-green-800",
	danger: "bg-red-100 text-red-800",
	neutral: "bg-gray-100 text-gray-800",
};

const factory: SliceFactory = (path, ctx, props) => ({
	type: "BadgeRef",
	value: null,
	label: typeof props?.label === "string" ? (props.label as string) : "",
	variant: typeof props?.variant === "string" ? (props.variant as string) : "neutral",
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as { label?: unknown; variant?: unknown };
			if ("label" in p) {
				slice.label = p.label == null ? "" : String(p.label);
			}
			if ("variant" in p) {
				slice.variant = p.variant == null ? "neutral" : String(p.variant);
			}
		}),
});

function BadgeView({ path }: { path: string }) {
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const variant = useStore((s) => (s.refs[path]?.variant as string) ?? "neutral");
	const cls = VARIANT_CLASSES[variant] ?? VARIANT_CLASSES.neutral;
	return (
		<span
			className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}
		>
			{label}
		</span>
	);
}

export const BadgeRef: RefEntry = { factory, component: BadgeView };
