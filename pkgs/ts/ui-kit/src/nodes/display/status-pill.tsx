// StatusPillRef -- a state as icon + label, readable without color.
//
// Server-owned. A write is a partial merge of `tone` / `label` into the
// node's props, which is the default store behaviour, so this type is a
// component and nothing else. Composes the kit StatusPill primitive, which
// draws each tone's own icon (danger a triangle, ok a check, warn and info
// an info mark, neutral a ring), so the state survives without color. An
// unknown tone reads as `neutral`.

import { StatusPill } from "../../components/ui/status-pill";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

type Tone = "danger" | "warn" | "ok" | "info" | "neutral";

const TONES: Record<string, Tone> = {
	danger: "danger",
	warn: "warn",
	ok: "ok",
	info: "info",
	neutral: "neutral",
};

function StatusPillView({ path }: NodeProps) {
	const tone = TONES[useStringProp(path, "tone", "neutral")] ?? "neutral";
	const label = useStringProp(path, "label");
	return <StatusPill tone={tone}>{label}</StatusPill>;
}

export const StatusPillRef: NodeEntry = { component: StatusPillView };
