// StatusDotRef -- a tone dot for a live state, the words left to its label.
//
// Server-owned. A write is a partial merge of `tone` / `label` / `pulse` into
// the node's props, which is the default store behaviour, so this type is a
// component and nothing else. An unknown tone reads as `neutral`. Composes
// the kit StatusDot primitive.

import { StatusDot } from "../../components/ui/status-dot";
import { type NodeEntry, type NodeProps, useBoolProp, useStringProp } from "../../tree";

type Tone = "neutral" | "info" | "ok" | "warn" | "danger";

const TONES: Record<string, Tone> = {
	neutral: "neutral",
	info: "info",
	ok: "ok",
	warn: "warn",
	danger: "danger",
};

function StatusDotView({ path }: NodeProps) {
	const tone = TONES[useStringProp(path, "tone", "neutral")] ?? "neutral";
	const label = useStringProp(path, "label");
	const pulse = useBoolProp(path, "pulse");
	return <StatusDot tone={tone} pulse={pulse} label={label || undefined} />;
}

export const StatusDotRef: NodeEntry = { component: StatusDotView };
