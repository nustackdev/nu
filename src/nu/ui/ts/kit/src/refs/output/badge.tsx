// BadgeRef -- display-only label with a variant tag.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. Class-level defaults
// come in on the mount field `props` and seed the slice. Composes the kit
// Badge primitive; variant maps to Badge tone.

import { Badge } from "../../components/ui/badge";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

// Ref variants stay `neutral | info | warn | ok | danger` on the wire.
// Badge primitive's tone slot is `default | secondary | outline | danger |
// warn | ok | info`; `neutral` reads as `outline` (transparent bg, muted border).
const VARIANT_TO_TONE: Record<string, "default" | "outline" | "danger" | "warn" | "ok" | "info"> = {
	info: "info",
	warn: "warn",
	ok: "ok",
	danger: "danger",
	neutral: "outline",
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
	const tone = VARIANT_TO_TONE[variant] ?? VARIANT_TO_TONE.neutral;
	return <Badge variant={tone}>{label}</Badge>;
}

export const BadgeRef: RefEntry = { factory, component: BadgeView };
