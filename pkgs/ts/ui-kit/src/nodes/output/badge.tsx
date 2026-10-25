// BadgeRef -- display-only label with a variant tag.
//
// Server-owned. A write is a partial merge of `label` / `variant` / `size`
// into the node's props, which is the default store behaviour, so this type
// is a component and nothing else. Nil reads back as the class default at render
// time. Composes the kit Badge primitive; variant maps to Badge tone.
//
// In a Line (inline flow) it is a chip on the text's baseline.

import { Badge } from "../../components/ui/badge";
import { lineChip } from "../../components/ui/line";
import { type NodeEntry, type NodeProps, useEnumProp, useFlow, useStringProp } from "../../tree";

// Ref variants are `neutral | brand | secondary | info | warn | ok | danger |
// dashed` on the wire. Badge primitive's tone slot is `default | secondary |
// outline | danger | warn | ok | info | dashed`; `neutral` reads as `outline`
// (transparent bg, muted border), `brand` as the Afterglow `default` chip
// (`default` itself is taken too, for parity with the kit), `secondary` as
// the Starlight one. `size` is the primitive's sm / md / lg.
const VARIANT_TO_TONE: Record<
	string,
	"default" | "secondary" | "outline" | "danger" | "warn" | "ok" | "info" | "dashed"
> = {
	brand: "default",
	default: "default",
	secondary: "secondary",
	info: "info",
	warn: "warn",
	ok: "ok",
	danger: "danger",
	neutral: "outline",
	dashed: "dashed",
};

const SIZES = ["sm", "md", "lg"] as const;

function BadgeView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const variant = useStringProp(path, "variant", "neutral");
	const tone = VARIANT_TO_TONE[variant] ?? VARIANT_TO_TONE.neutral;
	const size = useEnumProp(path, "size", SIZES, "md");
	const inline = useFlow() === "inline";
	return (
		<Badge variant={tone} size={size} className={inline ? lineChip : undefined}>
			{label}
		</Badge>
	);
}

export const BadgeRef: NodeEntry = { component: BadgeView };
