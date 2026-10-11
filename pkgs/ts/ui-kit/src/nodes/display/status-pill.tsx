// StatusPillRef -- status as icon + label, readable without color. STUB: the
// smallest honest draw with the StatusPill primitive; the display unit owns
// tone validation and the setters.

import { StatusPill } from "../../components/ui/status-pill";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

const TONES = new Set(["neutral", "info", "ok", "warn", "danger"]);

type Tone = "neutral" | "info" | "ok" | "warn" | "danger";

function StatusPillView({ path }: NodeProps) {
	const tone = useStringProp(path, "tone", "neutral");
	const label = useStringProp(path, "label");
	return <StatusPill tone={(TONES.has(tone) ? tone : "neutral") as Tone}>{label}</StatusPill>;
}

export const StatusPillRef: NodeEntry = { component: StatusPillView };
