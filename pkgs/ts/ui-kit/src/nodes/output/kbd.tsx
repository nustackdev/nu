// KbdRef -- one key cap, display only.
//
// Server-owned. A write is a partial merge of `label` / `variant` / `size`
// into the node's props, the default store behaviour, so this type is a
// component and nothing else. Composes the kit Kbd primitive. The label is
// drawn as given; a combination spelled per platform is a ShortcutRef.

import { Kbd } from "../../components/ui/kbd";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

type Variant = "default" | "ghost";
type Size = "sm" | "md";

const VARIANTS = new Set<Variant>(["default", "ghost"]);
const SIZES = new Set<Size>(["sm", "md"]);

function KbdView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const variant = useStringProp(path, "variant", "default") as Variant;
	const size = useStringProp(path, "size", "md") as Size;
	return (
		<Kbd variant={VARIANTS.has(variant) ? variant : "default"} size={SIZES.has(size) ? size : "md"}>
			{label}
		</Kbd>
	);
}

export const KbdRef: NodeEntry = { component: KbdView };
