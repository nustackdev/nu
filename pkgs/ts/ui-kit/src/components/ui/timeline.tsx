// Timeline primitive. Lanes over one time window: a label on the left (a
// page link: mark and title), a track of intervals in the middle, the lane's
// count on the right, a time axis under them all.
// Design refs:
//   palette.md       status tones for bars, text-muted for neutral,
//                    border-subtle for the track rule
//   form.md          lines over boxes: the track is a hairline, bars sit on it
//   cursor.md        lane labels are in-app navigation, they keep the arrow
//   typography.md    text-sm labels, text-xs counts and ticks, tabular nums
//
// Generic: colored intervals on a time axis. An item is a bar from its start
// to its end, placed in percent of the window, so it needs no layout pass,
// and colored by the tone the caller gives it. One too short to see still
// gets `MIN_BAR` px, so it reads as a tick. One with no end is drawn to the
// window's end, the same as any other bar. What a tone means is the
// caller's: `legend` names the tones it uses.
//
// Items of one lane may overlap (one job running twice at once). They
// are packed into sub-rows, first fit by start, so no bar hides another: one
// row draws an 8px bar, two rows 6px each, three rows 4px each. Past three
// rows the bars wrap onto the three and draw at partial opacity, so a stack
// of them reads darker where more items overlap, and nothing is dropped.
//
// One tooltip per timeline, not one per bar: the track finds the bar under
// the pointer and the tooltip anchors to a stand-in placed over it. A
// hundred bars a lane over twenty lanes stays two thousand plain spans.
//
// Capping is honest. Past `maxLanes` the rest is a "+N more" row, N counted
// from `totalLanes` when the host knows more lanes than it sent. Past
// `maxItems` a lane draws its danger items and then its newest ones, and the
// count on the right is still the lane's full count.
//
// Times are numbers on one scale, epoch ms (what `Date.now()` gives and what
// the axis and tooltip format). The window is any span, seconds to weeks;
// the axis words its ticks to fit ("15m", "2h 30m", "3d ago").

import type { LucideIcon } from "lucide-react";
import * as React from "react";

import { formatCount, formatFullCount } from "../../lib/count";
import { cn } from "../../lib/utils";
import { Icon } from "./icon";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";

export const TIMELINE_TONES = ["neutral", "info", "ok", "warn", "danger"] as const;
export type TimelineTone = (typeof TIMELINE_TONES)[number];

export interface TimelineItem {
	start: number;
	/** Unset or null: no end yet, the bar reaches the window's end. */
	end?: number | null;
	/** The bar's color. Default "neutral". */
	tone?: TimelineTone;
	/** Leads the tooltip: an id, a name, what started it. */
	label?: string;
}

export interface TimelineLane {
	/** Stable key; falls back to the lane's index. */
	id?: string;
	title: React.ReactNode;
	/** The lane's glyph. Wins over `mark`. */
	icon?: LucideIcon;
	/** A text mark: an emoji or a letter. */
	mark?: React.ReactNode;
	/** Where the label goes. No href draws the label as plain text. */
	href?: string;
	target?: "_self" | "_blank";
	/** Replaces the whole left cell: a slot for a host's own page link. */
	label?: React.ReactNode;
	items: TimelineItem[];
	/** The lane's full count, when the host sent fewer items than there are. */
	count?: number;
	/**
	 * Words for the count cell in place of the counted ones ("100+ jobs"), for a
	 * host that knows only a lower bound. `count` still sets the full-count title.
	 */
	countLabel?: string;
}

export type TimelineAxis = "relative" | "clock" | "none";

export interface TimelineProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "children"> {
	/** Window start and end, epoch ms. */
	start: number;
	end: number;
	lanes: TimelineLane[];
	/** How many lanes there are in all, when the host sent only some. */
	totalLanes?: number;
	/** Lanes drawn before the "+N more" row. 0 draws every lane sent. */
	maxLanes?: number;
	/** Items drawn per lane. Danger ones first, then the newest. */
	maxItems?: number;
	/** What an item is called in the count: "job" reads "1 job", "48 jobs". */
	noun?: string;
	nounPlural?: string;
	/** "relative" ticks count back from the end ("60m ago" .. "now"), "clock" shows times. */
	axis?: TimelineAxis;
	/** Names for the tones in use ({ok: "ok", danger: "failed"}): the legend and the tooltips. */
	legend?: Partial<Record<TimelineTone, string>>;
	/** The words after "+N" in the more row. */
	moreLabel?: string;
	/** Trailing slot of the more row: a way to see them all. */
	more?: React.ReactNode;
	/** A quiet line under the lanes: what the lanes are, where the rest are. */
	note?: React.ReactNode;
}

// --- numbers and time ------------------------------------------------------

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/**
 * A duration as a tick reads it: "45s", "15m", "2h 30m", "3d", "1d 6h". The
 * smaller part shows only when the span is short enough for it to matter.
 */
export function formatDuration(ms: number, span: number): string {
	if (span < 2 * MINUTE) return `${Math.round(ms / SECOND)}s`;
	const mins = Math.round(ms / MINUTE);
	if (span <= 3 * HOUR) return `${mins}m`;
	if (span <= 2 * DAY) {
		const h = Math.floor(mins / 60);
		const m = mins % 60;
		return m && span <= 12 * HOUR ? `${h}h ${m}m` : `${Math.round(mins / 60)}h`;
	}
	const hours = Math.round(ms / HOUR);
	const d = Math.floor(hours / 24);
	const h = hours % 24;
	if (d === 0) return `${h}h`;
	return h && span <= 14 * DAY ? `${d}d ${h}h` : `${Math.round(hours / 24)}d`;
}

/** How long an interval lasted, two parts at most: "0.4s", "12s", "3m 20s", "2h 5m", "1d 3h". */
export function formatLength(ms: number): string {
	if (ms < 10 * SECOND) return `${Math.round(ms / 100) / 10}s`;
	const parts: [number, string][] = [
		[Math.floor(ms / DAY), "d"],
		[Math.floor(ms / HOUR) % 24, "h"],
		[Math.floor(ms / MINUTE) % 60, "m"],
		[Math.floor(ms / SECOND) % 60, "s"],
	];
	const first = parts.findIndex(([n]) => n > 0);
	return parts
		.slice(first, first + 2)
		.filter(([n]) => n > 0)
		.map(([n, u]) => `${n}${u}`)
		.join(" ");
}

function formatAgo(ms: number, span: number, first: boolean): string {
	if (ms <= 0) return "now";
	const d = formatDuration(ms, span);
	return first ? `${d} ago` : d;
}

const clockFormat = new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" });
const secondsFormat = new Intl.DateTimeFormat(undefined, {
	hour: "2-digit",
	minute: "2-digit",
	second: "2-digit",
});
const dayFormat = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
const dayClockFormat = new Intl.DateTimeFormat(undefined, {
	month: "short",
	day: "numeric",
	hour: "2-digit",
	minute: "2-digit",
});

function formatClock(t: number, span: number): string {
	return span > 2 * DAY ? dayFormat.format(t) : clockFormat.format(t);
}

/** A moment in a tooltip, as fine as the window needs. */
function formatMoment(t: number, span: number): string {
	if (span > DAY) return dayClockFormat.format(t);
	return span <= HOUR ? secondsFormat.format(t) : clockFormat.format(t);
}

/** Five ticks over the window, start to end. The first relative one says "ago". */
export function timelineTicks(start: number, end: number, axis: TimelineAxis): string[] {
	const span = end - start;
	return [0, 1, 2, 3, 4].map((i) => {
		const t = start + (span * i) / 4;
		return axis === "clock" ? formatClock(t, span) : formatAgo(end - t, span, i === 0);
	});
}

// --- layout ----------------------------------------------------------------

/** Sub-rows a lane draws before overlapping bars wrap and stack. */
const MAX_ROWS = 3;
/** The narrowest a bar draws, px: an item too short to see reads as a tick. */
const MIN_BAR = 3;

export interface TimelineMark {
	item: TimelineItem;
	tone: TimelineTone;
	/** No end: the bar reaches the window's end. */
	open: boolean;
	/** Left edge, percent of the track. */
	left: number;
	/** Width, percent of the track, before the MIN_BAR floor. */
	width: number;
	/** Sub-row, 0 at the top. */
	row: number;
	/** Wrapped onto a row it shares with an overlapping bar, past MAX_ROWS. */
	stacked: boolean;
}

export interface TimelineLayout {
	marks: TimelineMark[];
	/** Sub-rows in use, 1 to MAX_ROWS. */
	rows: number;
}

/**
 * The items a lane draws, capped at `maxItems`: danger ones first, so a
 * problem is never what is left out, then the newest. Pure, so a test can read it.
 */
export function capItems(items: TimelineItem[], maxItems: number): TimelineItem[] {
	if (maxItems <= 0 || items.length <= maxItems) return items;
	const danger: TimelineItem[] = [];
	const rest: TimelineItem[] = [];
	for (const it of items) (it.tone === "danger" ? danger : rest).push(it);
	rest.sort((a, b) => b.start - a.start);
	return [...danger.slice(0, maxItems), ...rest.slice(0, Math.max(0, maxItems - danger.length))];
}

/**
 * Where each item sits on the track, in percent, and which sub-row it takes.
 * Overlapping items go first fit by start into rows; past MAX_ROWS one
 * wraps onto the row that frees up first and is marked stacked. Items wholly
 * outside the window drop out of the drawing only.
 */
export function layoutItems(items: TimelineItem[], start: number, end: number): TimelineLayout {
	const span = end - start;
	if (!(span > 0)) return { marks: [], rows: 1 };
	const sorted = items
		.filter((it) => it.start <= end && (it.end ?? end) >= start)
		.sort((a, b) => a.start - b.start);
	// Each row's end time; an item takes the first row free at its start.
	const rowEnds: number[] = [];
	const marks: TimelineMark[] = [];
	let stackedAny = false;
	for (const item of sorted) {
		const a = Math.max(item.start, start);
		const b = Math.min(item.end ?? end, end);
		let row = rowEnds.findIndex((e) => e <= item.start);
		let stacked = false;
		if (row === -1) {
			if (rowEnds.length < MAX_ROWS) {
				row = rowEnds.length;
				rowEnds.push(0);
			} else {
				row = rowEnds.indexOf(Math.min(...rowEnds));
				stacked = true;
				stackedAny = true;
			}
		}
		rowEnds[row] = Math.max(rowEnds[row], item.end ?? end);
		marks.push({
			item,
			tone: item.tone ?? "neutral",
			open: item.end == null,
			left: ((a - start) / span) * 100,
			width: (Math.max(0, b - a) / span) * 100,
			row,
			stacked,
		});
	}
	// Once any bar stacks, the rest of its rows can too: draw every bar of the
	// lane at the same partial opacity so overlaps read by density alone.
	if (stackedAny) for (const m of marks) m.stacked = true;
	return { marks, rows: Math.max(1, rowEnds.length) };
}

// --- looks -----------------------------------------------------------------

const BAR_CLASS: Record<TimelineTone, string> = {
	neutral: "bg-text-secondary/40",
	info: "bg-status-info",
	ok: "bg-status-ok",
	warn: "bg-status-warn",
	danger: "bg-status-danger",
};

// Bar geometry per row count on a 24px track: [top of row 0, height, step].
const ROW_GEOMETRY: Record<number, [number, number, number]> = {
	1: [8, 8, 0],
	2: [5, 6, 8],
	3: [4, 4, 6],
};

// label | track | count. The label column holds a title and a 14px mark; the
// count column fits "48.2K items".
const GRID = "grid grid-cols-[minmax(0,12rem)_minmax(0,1fr)_4.5rem] items-center gap-3";

type Hover = { lane: number; index: number } | null;

function ItemTip({ mark, span, name }: { mark: TimelineMark; span: number; name?: string }) {
	const { item } = mark;
	const end = item.end ?? null;
	const when =
		end === null
			? `from ${formatMoment(item.start, span)}`
			: `${formatMoment(item.start, span)} to ${formatMoment(end, span)}`;
	return (
		<span className="flex flex-col gap-0.5">
			{item.label ? <span className="font-medium">{item.label}</span> : null}
			<span className="tabular-nums">{name ? `${name} · ${when}` : when}</span>
			{end !== null ? (
				<span className="tabular-nums text-text-secondary">{formatLength(end - item.start)}</span>
			) : null}
		</span>
	);
}

function Track({
	layout,
	label,
	span,
	names,
	hovered,
	onHover,
}: {
	layout: TimelineLayout;
	label: string;
	span: number;
	names: Partial<Record<TimelineTone, string>>;
	hovered: number | null;
	onHover: (index: number | null) => void;
}) {
	const [top0, height, step] = ROW_GEOMETRY[layout.rows] ?? ROW_GEOMETRY[MAX_ROWS];
	const place = (m: TimelineMark): React.CSSProperties => ({
		left: `${m.left}%`,
		width: `${m.width}%`,
		minWidth: MIN_BAR,
		top: top0 + m.row * step,
		height,
	});
	const hit = hovered === null ? null : layout.marks[hovered];
	return (
		<div
			data-slot="timeline-track"
			role="img"
			aria-label={label}
			className="relative h-6"
			onPointerOver={(e) => {
				const el = (e.target as HTMLElement).closest<HTMLElement>("[data-index]");
				onHover(el ? Number(el.dataset.index) : null);
			}}
			onPointerLeave={() => onHover(null)}
		>
			<div aria-hidden="true" className="absolute inset-x-0 top-1/2 h-px bg-border-subtle" />
			{layout.marks.map((m, i) => (
				<span
					// biome-ignore lint/suspicious/noArrayIndexKey: data-index is the hover lookup, marks are positional
					key={i}
					data-index={i}
					data-slot="timeline-bar"
					data-tone={m.tone}
					aria-hidden="true"
					className={cn(
						"absolute rounded-sm",
						BAR_CLASS[m.tone],
						m.stacked && "opacity-70",
						i === hovered && "ring-1 ring-text-primary",
					)}
					style={place(m)}
				/>
			))}
			{hit && (
				// Remounted per bar, so the tooltip measures its new anchor.
				<Tooltip key={hovered} open>
					<TooltipTrigger asChild>
						<span aria-hidden="true" className="pointer-events-none absolute" style={place(hit)} />
					</TooltipTrigger>
					<TooltipContent side="top">
						<ItemTip mark={hit} span={span} name={names[hit.tone]} />
					</TooltipContent>
				</Tooltip>
			)}
		</div>
	);
}

function LaneLabel({ lane }: { lane: TimelineLane }) {
	if (lane.label !== undefined) return <>{lane.label}</>;
	const mark = lane.icon ? (
		<Icon icon={lane.icon} size="sm" className="text-text-muted" />
	) : lane.mark ? (
		<span aria-hidden="true" className="w-3.5 shrink-0 text-center leading-none">
			{lane.mark}
		</span>
	) : null;
	const body = (
		<>
			{mark}
			<span className="truncate">{lane.title}</span>
		</>
	);
	const base =
		"flex min-w-0 items-center gap-2 rounded-sm px-1 -mx-1 h-6 text-sm text-text-secondary";
	if (!lane.href) {
		return (
			<span data-slot="timeline-label" className={base}>
				{body}
			</span>
		);
	}
	const blank = lane.target === "_blank";
	return (
		<a
			data-slot="timeline-label"
			href={lane.href}
			target={blank ? "_blank" : undefined}
			rel={blank ? "noopener noreferrer" : undefined}
			className={cn(
				base,
				"cursor-default no-underline focus-ring",
				"transition-colors duration-fast ease-out",
				"hover:bg-bg-hover hover:text-text-primary active:bg-bg-press",
			)}
		>
			{body}
		</a>
	);
}

export interface TimelineLegendProps extends React.HTMLAttributes<HTMLDivElement> {
	/** A name per tone, drawn in tone order. A tone with no name is left out. */
	names: Partial<Record<TimelineTone, string>>;
}

/** The key to a timeline's tones. The Timeline draws its own; this is for a host that puts it in a header. */
export function TimelineLegend({ names, className, ...props }: TimelineLegendProps) {
	return (
		<div
			data-slot="timeline-legend"
			className={cn("flex flex-wrap items-center gap-3 text-xs text-text-muted", className)}
			{...props}
		>
			{TIMELINE_TONES.filter((t) => names[t]).map((t) => (
				<span key={t} className="inline-flex items-center gap-1.5">
					<span aria-hidden="true" className={cn("size-2.5 rounded-sm", BAR_CLASS[t])} />
					{names[t]}
				</span>
			))}
		</div>
	);
}

export function Timeline({
	start,
	end,
	lanes,
	totalLanes,
	maxLanes = 10,
	maxItems = 100,
	noun = "item",
	nounPlural,
	axis = "relative",
	legend,
	moreLabel = "more",
	more,
	note,
	className,
	...props
}: TimelineProps) {
	const [hover, setHover] = React.useState<Hover>(null);
	const shown = React.useMemo(
		() => (maxLanes > 0 ? lanes.slice(0, maxLanes) : lanes),
		[lanes, maxLanes],
	);
	const left = Math.max(totalLanes ?? lanes.length, lanes.length) - shown.length;
	const plural = nounPlural ?? `${noun}s`;
	const span = end - start;
	const laid = React.useMemo(
		() => shown.map((lane) => layoutItems(capItems(lane.items, maxItems), start, end)),
		[shown, maxItems, start, end],
	);
	// The legend keys what is drawn and named, nothing else.
	const names = legend ?? {};
	const present: Partial<Record<TimelineTone, string>> = {};
	for (const l of laid) for (const m of l.marks) if (names[m.tone]) present[m.tone] = names[m.tone];
	return (
		<TooltipProvider delayDuration={0}>
			<div data-slot="timeline" className={cn("flex flex-col", className)} {...props}>
				{Object.keys(present).length > 0 && (
					<TimelineLegend className="mb-2 justify-end" names={present} />
				)}
				{shown.map((lane, i) => {
					const count = lane.count ?? lane.items.length;
					const countText =
						lane.countLabel || `${formatCount(count)} ${count === 1 ? noun : plural}`;
					const title = typeof lane.title === "string" ? lane.title : "";
					return (
						<div key={lane.id ?? i} data-slot="timeline-lane" className={cn(GRID, "h-6")}>
							<LaneLabel lane={lane} />
							<Track
								layout={laid[i]}
								label={title ? `${title}: ${countText}` : countText}
								span={span}
								names={names}
								hovered={hover?.lane === i ? hover.index : null}
								onHover={(index) => setHover(index === null ? null : { lane: i, index })}
							/>
							<span
								data-slot="timeline-count"
								title={formatFullCount(count)}
								className="text-right text-xs tabular-nums text-text-muted"
							>
								{countText}
							</span>
						</div>
					);
				})}
				{left > 0 && (
					<div data-slot="timeline-more" className={cn(GRID, "h-7 text-sm text-text-muted")}>
						<span>
							<b className="font-medium tabular-nums text-text-secondary">+{formatCount(left)}</b>{" "}
							{moreLabel}
						</span>
						<span />
						<span className="flex justify-end">{more}</span>
					</div>
				)}
				{axis !== "none" && (
					<div data-slot="timeline-axis" aria-hidden="true" className={cn(GRID, "mt-1.5")}>
						<span />
						<div className="flex justify-between text-xs tabular-nums text-text-muted">
							{timelineTicks(start, end, axis).map((t, i) => (
								// biome-ignore lint/suspicious/noArrayIndexKey: five fixed ticks, labels can repeat
								<span key={i}>{t}</span>
							))}
						</div>
						<span />
					</div>
				)}
				{note && (
					<p data-slot="timeline-note" className="mt-2 text-xs text-text-muted">
						{note}
					</p>
				)}
			</div>
		</TooltipProvider>
	);
}
