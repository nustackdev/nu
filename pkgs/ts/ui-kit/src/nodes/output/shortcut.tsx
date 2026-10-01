// ShortcutRef -- a key combination by key name, display only.
//
// Server-owned. A write is a partial merge of `keys` / `variant` / `size`
// into the node's props, the default store behaviour, so this type is a
// component and nothing else. Composes the kit Shortcut primitive, which
// spells the keys for the reader's platform (`mod` is command on a Mac,
// control elsewhere), so the server names keys and never platforms.

import { Shortcut } from "../../components/ui/shortcut";
import { type NodeEntry, type NodeProps, useListProp, useStringProp } from "../../tree";

type Variant = "default" | "ghost";
type Size = "sm" | "md";

const VARIANTS = new Set<Variant>(["default", "ghost"]);
const SIZES = new Set<Size>(["sm", "md"]);

function ShortcutView({ path }: NodeProps) {
	const keys = useListProp<string>(path, "keys");
	const variant = useStringProp(path, "variant", "default") as Variant;
	const size = useStringProp(path, "size", "md") as Size;
	return (
		<Shortcut
			keys={keys.map(String)}
			variant={VARIANTS.has(variant) ? variant : "default"}
			size={SIZES.has(size) ? size : "md"}
		/>
	);
}

export const ShortcutRef: NodeEntry = { component: ShortcutView };
