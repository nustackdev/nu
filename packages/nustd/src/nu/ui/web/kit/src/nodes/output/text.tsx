// TextRef -- display-only paragraph string. Renders via kit Text primitive.
//
// Server-owned, and there is nothing to do on a write: the default store
// behaviour lands a bare payload on `value`, so this type is a component and
// nothing else. Nil payload (Nu sentinel) reads back as the empty string at
// render time. Wire strings often carry `\n`; whitespace is preserved here.

import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

function TextView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	return (
		<Text as="p" size="base" tone="primary" className="whitespace-pre-wrap">
			{value}
		</Text>
	);
}

export const TextRef: NodeEntry = { component: TextView };
