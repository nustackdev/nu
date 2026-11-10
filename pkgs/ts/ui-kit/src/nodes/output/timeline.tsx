// TimelineRef -- lanes of intervals over one time window, with an axis and
// an honest "+N more" row.
//
// Server-owned, plain props merged by the default store `write`:
//   start, end      the window, epoch ms
//   lanes           [{id, title, icon, href, target, count, count_label, items}], items as
//                   [start, end, tone, label] lists (end null: no end yet;
//                   tone and label optional) or {start, end, tone, label}
//                   objects, both read alike
//   total_lanes     how many lanes there are in all; past what was sent, the
//                   rest is counted in the more row
//   max_lanes       lanes before the more row, 0 for all of them
//   max_items, noun, noun_plural, axis
//   legend          {tone: name}: the legend and the tooltips name the tones
//   more_label      the words after "+N"
//   more_text, more_href, more_target
//                   a way to see them all, a ghost link in the more row
//   note            a quiet line under the lanes
//
// `icon` is a lucide name or any short text drawn as is (an emoji), the same
// as PageLinkRef. A lane with an href is a real <a>, so a host's
// AnchorCatcher routes it. Everything off the wire is checked at read time:
// a malformed item or lane drops out of the drawing, never the render.

import { ArrowRight } from "lucide-react";
import { Button } from "../../components/ui/button";
import {
	TIMELINE_TONES,
	Timeline,
	type TimelineItem,
	type TimelineLane,
	type TimelineTone,
} from "../../components/ui/timeline";
import { anchorProps, normTarget } from "../../lib/anchor";
import { iconFor, isIconName } from "../../lib/icons";
import {
	type NodeEntry,
	type NodeProps,
	useEnumProp,
	useListProp,
	useNumberProp,
	useProp,
	useStringProp,
} from "../../tree";

const AXES = ["relative", "clock", "none"] as const;
const TONES = new Set<string>(TIMELINE_TONES);

function num(v: unknown): number | null {
	return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function tone(v: unknown): TimelineTone {
	return typeof v === "string" && TONES.has(v) ? (v as TimelineTone) : "neutral";
}

function text(v: unknown): string | undefined {
	return typeof v === "string" && v !== "" ? v : undefined;
}

/** One item off the wire: a [start, end, tone, label] list or an object. */
export function readItem(raw: unknown): TimelineItem | null {
	if (Array.isArray(raw)) {
		const start = num(raw[0]);
		if (start === null) return null;
		return { start, end: num(raw[1]), tone: tone(raw[2]), label: text(raw[3]) };
	}
	if (raw && typeof raw === "object") {
		const o = raw as Record<string, unknown>;
		const start = num(o.start);
		if (start === null) return null;
		return { start, end: num(o.end), tone: tone(o.tone), label: text(o.label) };
	}
	return null;
}

/** One lane off the wire. */
export function readLane(raw: unknown, index: number): TimelineLane | null {
	if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
	const o = raw as Record<string, unknown>;
	const str = (k: string) => (typeof o[k] === "string" ? (o[k] as string) : "");
	const items: TimelineItem[] = [];
	if (Array.isArray(o.items)) {
		for (const r of o.items) {
			const it = readItem(r);
			if (it) items.push(it);
		}
	}
	const icon = str("icon");
	const glyph = isIconName(icon) ? (iconFor(icon) ?? undefined) : undefined;
	const href = str("href");
	const count = num(o.count);
	return {
		id: str("id") || String(index),
		title: str("title") || href,
		icon: glyph,
		mark: glyph ? undefined : icon || undefined,
		href: href || undefined,
		target: normTarget(str("target")),
		items,
		count: count === null ? undefined : Math.max(0, Math.round(count)),
		countLabel: str("count_label") || undefined,
	};
}

/** The tone names off the wire: known tones with a string name, nothing else. */
export function readLegend(raw: unknown): Partial<Record<TimelineTone, string>> {
	const out: Partial<Record<TimelineTone, string>> = {};
	if (!raw || typeof raw !== "object" || Array.isArray(raw)) return out;
	for (const [k, v] of Object.entries(raw)) {
		if (TONES.has(k) && typeof v === "string" && v) out[k as TimelineTone] = v;
	}
	return out;
}

function TimelineView({ path }: NodeProps) {
	const end = useNumberProp(path, "end", 0);
	const start = useNumberProp(path, "start", 0);
	const rawLanes = useListProp<unknown>(path, "lanes");
	const totalLanes = useNumberProp(path, "total_lanes", 0);
	const maxLanes = useNumberProp(path, "max_lanes", 10);
	const maxItems = useNumberProp(path, "max_items", 100);
	const noun = useStringProp(path, "noun", "item");
	const nounPlural = useStringProp(path, "noun_plural");
	const axis = useEnumProp(path, "axis", AXES, "relative");
	const legend = readLegend(useProp<unknown>(path, "legend", null));
	const moreLabel = useStringProp(path, "more_label", "more");
	const moreText = useStringProp(path, "more_text");
	const moreHref = useStringProp(path, "more_href");
	const moreTarget = useStringProp(path, "more_target", "_self");
	const note = useStringProp(path, "note");

	const lanes: TimelineLane[] = [];
	rawLanes.forEach((raw, i) => {
		const lane = readLane(raw, i);
		if (lane) lanes.push(lane);
	});
	const more =
		moreText && moreHref ? (
			<Button variant="ghost" size="sm" asChild>
				<a {...anchorProps(moreHref, moreTarget)}>
					{moreText}
					<ArrowRight />
				</a>
			</Button>
		) : undefined;

	return (
		<Timeline
			start={start}
			end={end}
			lanes={lanes}
			totalLanes={totalLanes > 0 ? totalLanes : undefined}
			maxLanes={maxLanes}
			maxItems={maxItems}
			noun={noun || "item"}
			nounPlural={nounPlural || undefined}
			axis={axis}
			legend={legend}
			moreLabel={moreLabel || "more"}
			more={more}
			note={note || undefined}
		/>
	);
}

// A timeline takes the width it is given, like a chart.
export const TimelineRef: NodeEntry = { component: TimelineView, fill: true };
