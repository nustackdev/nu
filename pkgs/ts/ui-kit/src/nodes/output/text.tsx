// TextRef -- display-only paragraph string. Renders via kit Text primitive.
//
// Server-owned, and there is nothing to do on a write: the default store
// behaviour lands a bare payload on `value`, so this type is a component and
// nothing else. Nil payload (Nu sentinel) reads back as the empty string at
// render time. Wire strings often carry `\n`; whitespace is preserved here.
//
// Its box carries the same 4px of vertical padding as Prose, so every text
// output has one edge: padding, never margin, so it cannot collapse or leak.

import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

function TextView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	return (
		<Text as="p" size="base" tone="primary" className="whitespace-pre-wrap py-1">
			{value}
		</Text>
	);
}

export const TextRef: NodeEntry = { component: TextView };
