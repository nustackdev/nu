// RelativeTimeRef -- a stamp drawn as time from now ("4m ago", "3m 12s"),
// kept live in the browser.
//
// Server-owned. A write is a partial merge of `ts` / `mode` into the node's
// props, which is the default store behaviour, so this type is a component
// and nothing else. `ts` is epoch ms; a missing one draws a muted "-". An
// unknown mode reads as `ago`. The server sends the stamp once and never
// redraws for the clock: the kit RelativeTime primitive ticks on its own.
//
// It is a span, so in a Line it is one piece of the sentence and takes the
// Line's type; in a block flow it reads as a small secondary label.

import { RELATIVE_TIME_MODES, RelativeTime } from "../../components/ui/relative-time";
import { type NodeEntry, type NodeProps, useEnumProp, useFlow, useProp } from "../../tree";

function RelativeTimeView({ path }: NodeProps) {
	const raw = useProp<unknown>(path, "ts", null);
	const ts = raw == null || raw === "" ? Number.NaN : Number(raw);
	const mode = useEnumProp(path, "mode", RELATIVE_TIME_MODES, "ago");
	const inline = useFlow() === "inline";
	return (
		<RelativeTime
			ts={ts}
			mode={mode}
			className={inline ? undefined : "text-sm text-text-secondary"}
		/>
	);
}

export const RelativeTimeRef: NodeEntry = { component: RelativeTimeView };
