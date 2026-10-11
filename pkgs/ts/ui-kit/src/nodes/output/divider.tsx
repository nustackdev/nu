// DividerRef -- display-only rule with optional inline label.
//
// The parent's flow decides the direction, there is no prop for it: inside a
// Row the divider stands vertical, 20px tall (the label is dropped, a
// vertical rule has no room for one), and grows to the row's height when the
// row stretches its children. Everywhere else it is a horizontal rule.
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
import { type NodeEntry, type NodeProps, useFlow, useStringProp } from "../../tree";

function DividerView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const flow = useFlow();
	if (flow === "row") {
		return <Separator orientation="vertical" className="mx-1 h-5 self-center" />;
	}
	return (
		<div className="my-4 w-full">
			<Separator label={label || undefined} />
		</div>
	);
}

export const DividerRef: NodeEntry = { component: DividerView };
