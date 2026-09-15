// BadgeRef -- display-only label with a variant tag.
//
// Server-owned. A write is a partial merge of `label` / `variant` into the
// node's props, which is the default store behaviour, so this type is a
// component and nothing else. Nil reads back as the class default at render
// time. Composes the kit Badge primitive; variant maps to Badge tone.

import { Badge } from "../../components/ui/badge";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

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

function BadgeView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const variant = useStringProp(path, "variant", "neutral");
	const tone = VARIANT_TO_TONE[variant] ?? VARIANT_TO_TONE.neutral;
	return <Badge variant={tone}>{label}</Badge>;
}

export const BadgeRef: NodeEntry = { component: BadgeView };
