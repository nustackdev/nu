// WaterfallRef -- spans on one time axis, like a trace view.
//
// Server-owned. A write is a partial merge of {spans, start, end, now,
// max_rows, label_width, selectable, selected} into the node's props, which
// is the default store behaviour, so there is no handler. Python ships each
// span as a dict of {id, label, start, end, tone, parent, detail}, times in
// ms; a span read here with no id takes its position. Nil on start, end or
// now leaves the window to the spans. Composes the kit Waterfall primitive.
//
// With `selectable`, a row click marks the span selected locally and sends a
// notify {event: "select", id, label, start, end, tone, parent}.

import { OPS } from "@nustackdev/ui-core";
import { Waterfall } from "../../components/ui/waterfall";
import { isTone, type WaterfallSpan } from "../../components/ui/waterfall-model";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useListProp,
	useNumberProp,
	useProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

function num(v: unknown): number | null {
	return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function str(v: unknown): string {
	return v == null ? "" : String(v);
}

export function toSpan(raw: unknown, i: number): WaterfallSpan | null {
	if (raw == null || typeof raw !== "object") return null;
	const r = raw as Record<string, unknown>;
	const start = num(r.start);
	if (start === null) return null;
	return {
		id: r.id == null || r.id === "" ? String(i) : String(r.id),
		label: str(r.label),
		start,
		end: num(r.end),
		tone: isTone(r.tone) ? r.tone : "neutral",
		parent: r.parent == null || r.parent === "" ? null : String(r.parent),
		detail: str(r.detail) || undefined,
	};
}

function WaterfallView({ path }: NodeProps) {
	const spans = useListProp<unknown>(path, "spans")
		.map(toSpan)
		.filter((s): s is WaterfallSpan => s !== null);
	const start = num(useProp<unknown>(path, "start", null)) ?? undefined;
	const end = num(useProp<unknown>(path, "end", null)) ?? undefined;
	const now = num(useProp<unknown>(path, "now", null)) ?? undefined;
	const maxRows = useNumberProp(path, "max_rows", 50);
	const labelWidth = useNumberProp(path, "label_width", 200);
	const selectable = useBoolProp(path, "selectable");
	const selected = useStringProp(path, "selected");
	const send = useSend(path);
	const setProps = useSetProps(path);
	return (
		<Waterfall
			spans={spans}
			start={start}
			end={end}
			now={now}
			maxRows={maxRows > 0 ? maxRows : 50}
			labelWidth={labelWidth > 0 ? labelWidth : 200}
			selected={selected || null}
			onSelect={
				selectable
					? (s) => {
							setProps({ selected: s.id });
							send(OPS.notify, {
								event: "select",
								id: s.id,
								label: s.label,
								start: s.start,
								end: s.end ?? null,
								tone: s.tone ?? "neutral",
								parent: s.parent ?? null,
							});
						}
					: undefined
			}
		/>
	);
}

export const WaterfallRef: NodeEntry = { component: WaterfallView };
