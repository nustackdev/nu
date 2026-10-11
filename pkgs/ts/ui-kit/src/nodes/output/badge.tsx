// BadgeRef -- display-only label with a variant tag.
//
// Server-owned. A write is a partial merge of `label` / `variant` into the
// node's props, which is the default store behaviour, so this type is a
// component and nothing else. Nil reads back as the class default at render
// time. Composes the kit Badge primitive; variant maps to Badge tone.
//
// In a Line (inline flow) it is a chip on the text's baseline.

import { Badge } from "../../components/ui/badge";
import { lineChip } from "../../components/ui/line";
import { type NodeEntry, type NodeProps, useFlow, useStringProp } from "../../tree";

// Ref variants stay `neutral | info | warn | ok | danger | dashed` on the
// wire. Badge primitive's tone slot is `default | secondary | outline |
// danger | warn | ok | info | dashed`; `neutral` reads as `outline`
// (transparent bg, muted border).
const VARIANT_TO_TONE: Record<
	string,
	"default" | "outline" | "danger" | "warn" | "ok" | "info" | "dashed"
> = {
	info: "info",
	warn: "warn",
	ok: "ok",
	danger: "danger",
	neutral: "outline",
	dashed: "dashed",
};

function BadgeView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const variant = useStringProp(path, "variant", "neutral");
	const tone = VARIANT_TO_TONE[variant] ?? VARIANT_TO_TONE.neutral;
	const inline = useFlow() === "inline";
	return (
		<Badge variant={tone} className={inline ? lineChip : undefined}>
			{label}
		</Badge>
	);
}

export const BadgeRef: NodeEntry = { component: BadgeView };
