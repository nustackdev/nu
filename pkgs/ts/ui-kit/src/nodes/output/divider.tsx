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
// `align` places the label: start / center / end, with left / right read as
// the older spelling of start / end.

import { Separator } from "../../components/ui/separator";
import { normAlign } from "../../lib/align";
import { type NodeEntry, type NodeProps, useFlow, useProp, useStringProp } from "../../tree";

function DividerView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const align = normAlign(useProp<unknown>(path, "align", "center"), "center");
	const flow = useFlow();
	if (flow === "row") {
		return <Separator orientation="vertical" className="mx-1 h-5 self-center" />;
	}
	return (
		<div className="my-4 w-full">
			<Separator label={label || undefined} labelAlign={align} />
		</div>
	);
}

export const DividerRef: NodeEntry = { component: DividerView };
