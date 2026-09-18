// DividerRef -- display-only horizontal rule with optional inline label.
//
// Server-owned. A write is a partial merge of `label` / `align` into the
// node's props, which is the default store behaviour, so there is no handler.
// Nil reads back as the class default at render time. Composes the kit
// Separator primitive, which owns the labeled layout when `label` is set.
//
// TODO(retune): Separator primitive centers the label; `align` (left/right)
// asymmetric side widths from the old Ref are not yet supported by the
// primitive. Left as-is until the primitive grows an align slot.

import { Separator } from "../../components/ui/separator";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

function DividerView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	return (
		<div className="my-4 w-full">
			<Separator label={label || undefined} />
		</div>
	);
}

export const DividerRef: NodeEntry = { component: DividerView };
