// Calendar heatmap primitive.
//
// A year of days as a grid: `weeks` columns (53 by default) of 7 rows, ending
// with the week that holds `end`. Each day's shade is its value's quartile
// among the window's non-zero days, so one huge day never washes the rest
// out. A day's value is a number or named parts ({jobs, builds}); the shade
// is the sum and the tooltip names each part. Header totals, the peak day
// and a Less/More legend are optional chrome.
//
// One shared tooltip, not one per day: 371 squares stay plain divs. The grid
// is one tab stop; arrows walk the days (left/right a week, up/down a day)
// and the tooltip follows, read out through a polite live region.
//
// Native SVG-free markup on kit tokens. Afterglow by default, for
// contribution: people acting. `accent-2` (Starlight) for system data.

import type * as React from "react";
import { useCallback, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { cn } from "../../lib/utils";
import {
	buildModel,
	type CalendarHeatmapLevel,
	type CalendarHeatmapValues,
	type CalendarHeatmapWeekStart,
	describeDay,
	describeParts,
	formatCount,
	formatDay,
	formatFull,
	noun,
	parseDay,
} from "./calendar-heatmap-model";

export type CalendarHeatmapTone = "accent" | "accent-2";

// Whole class strings, so Tailwind finds every one.
const LEVEL_CLASS: Record<CalendarHeatmapTone, Record<CalendarHeatmapLevel, string>> = {
	accent: {
		0: "bg-bg-press",
		1: "bg-accent/30",
		2: "bg-accent/55",
		3: "bg-accent/80",
		4: "bg-accent",
	},
	"accent-2": {
		0: "bg-bg-press",
		1: "bg-accent-2/30",
		2: "bg-accent-2/55",
		3: "bg-accent-2/80",
		4: "bg-accent-2",
	},
};

const LEVELS: CalendarHeatmapLevel[] = [0, 1, 2, 3, 4];

// Square 8px plus a 3px gap: one week column is 11px.
const STEP = 11;
// Room a three-letter month label needs at text-xs. A label closer than this
// to the grid's right edge is anchored to that edge instead of its week, so
// it never pokes past the grid and makes the scroller scroll a few px.
const MONTH_LABEL_ROOM = 26;

const DAY_LABELS: Record<CalendarHeatmapWeekStart, string[]> = {
	mon: ["Mon", "", "Wed", "", "Fri", "", ""],
	sun: ["", "Mon", "", "Wed", "", "Fri", ""],
};

export interface CalendarHeatmapProps
	extends Omit<React.HTMLAttributes<HTMLDivElement>, "children" | "title"> {
	/** Day `YYYY-MM-DD` to a count, or to named counts ({jobs: 2, builds: 7}). */
	values: CalendarHeatmapValues;
	/** Last day shown, `YYYY-MM-DD` or a Date. Defaults to today. */
	end?: string | Date;
	weeks?: number;
	weekStart?: CalendarHeatmapWeekStart;
	tone?: CalendarHeatmapTone;
	/** Header label, left of the totals. */
	title?: string;
	/** Plural noun for plain number values ("commits"). Part keys name themselves. */
	unit?: string;
	/** Word after a day's counts: "finished" reads "2 jobs, 7 builds finished". */
	suffix?: string;
	/** Lead of the peak line ("Busiest"). Empty hides it. */
	peakLabel?: string;
	showTotals?: boolean;
	showLegend?: boolean;
}

function CalendarHeatmap({
	className,
	values,
	end,
	weeks = 53,
	weekStart = "mon",
	tone = "accent",
	title,
	unit = "",
	suffix = "",
	peakLabel = "Busiest",
	showTotals = true,
	showLegend = true,
	...props
}: CalendarHeatmapProps) {
	const endKey = end instanceof Date ? end.getTime() : (end ?? "");
	const model = useMemo(() => {
		const last =
			endKey === "" ? new Date() : typeof endKey === "number" ? new Date(endKey) : parseDay(endKey);
		return buildModel(values, last ?? new Date(), Math.max(1, Math.floor(weeks)), weekStart);
	}, [values, endKey, weeks, weekStart]);

	const [active, setActive] = useState<number | null>(null);
	const [keyboard, setKeyboard] = useState(false);
	const gridRef = useRef<HTMLDivElement>(null);
	const scrollRef = useRef<HTMLDivElement>(null);

	// When the container is narrower than the grid, open on the latest weeks.
	useLayoutEffect(() => {
		const el = scrollRef.current;
		if (el && model.days.length > 0) el.scrollLeft = el.scrollWidth;
	}, [model]);

	const levels = LEVEL_CLASS[tone];
	const cells = useMemo(
		() =>
			model.days.map((d, i) => (
				<div
					key={d.key}
					data-i={i}
					data-level={d.level ?? undefined}
					className={cn(
						"size-2 rounded-[2px]",
						d.level === null ? "bg-transparent" : levels[d.level],
						i === active && d.level !== null && "outline outline-1 outline-text-secondary",
					)}
				/>
			)),
		[model, levels, active],
	);

	const lastIndex = useMemo(() => {
		for (let i = model.days.length - 1; i >= 0; i--) if (model.days[i].level !== null) return i;
		return 0;
	}, [model]);

	const activeDay = active === null ? null : model.days[active];
	const tip = activeDay && activeDay.level !== null ? describeDay(activeDay, unit, suffix) : "";

	const onPointerMove = useCallback((e: React.PointerEvent) => {
		const i = (e.target as HTMLElement).dataset.i;
		setKeyboard(false);
		setActive(i === undefined ? null : Number(i));
	}, []);

	const onKeyDown = (e: React.KeyboardEvent) => {
		const step: Record<string, number> = {
			ArrowLeft: -7,
			ArrowRight: 7,
			ArrowUp: -1,
			ArrowDown: 1,
		};
		let next: number | null = null;
		const from = active ?? lastIndex;
		if (e.key in step) next = from + step[e.key];
		else if (e.key === "Home") next = 0;
		else if (e.key === "End") next = lastIndex;
		else if (e.key === "Escape") {
			setActive(null);
			return;
		} else return;
		e.preventDefault();
		setKeyboard(true);
		setActive(Math.max(0, Math.min(lastIndex, next)));
	};

	const label = title || "Calendar heatmap";
	const gridWidth = (model.days.length / 7) * STEP - 3;
	const totals = showTotals && model.totals.length > 0 && model.totals.some(([, n]) => n > 0);

	return (
		<div
			data-slot="calendar-heatmap"
			className={cn("inline-flex max-w-full flex-col gap-2 text-xs text-text-muted", className)}
			{...props}
		>
			{(title || totals) && (
				<div data-slot="calendar-heatmap-header" className="flex items-baseline gap-2">
					{title && <span>{title}</span>}
					<span className="flex-1" />
					{totals && (
						<span className="tabular-nums">
							{model.totals.map(([k, n], i) => {
								const name = noun(k || unit, n);
								return (
									<span key={k || "_"}>
										{i > 0 && ", "}
										<b className="font-semibold text-text-primary" title={formatFull(n)}>
											{formatCount(n)}
										</b>
										{name && ` ${name}`}
									</span>
								);
							})}
						</span>
					)}
				</div>
			)}

			<div ref={scrollRef} data-slot="calendar-heatmap-scroll" className="overflow-x-auto">
				<div className="grid w-max grid-cols-[26px_auto] gap-x-1.5">
					<div />
					<div className="relative h-[15px]" aria-hidden="true">
						{model.months.map((m) => (
							<span
								key={m.week}
								className="absolute top-0 whitespace-nowrap"
								style={
									gridWidth - m.week * STEP < MONTH_LABEL_ROOM
										? { right: 0 }
										: { left: m.week * STEP }
								}
							>
								{m.label}
							</span>
						))}
					</div>
					<div className="grid grid-rows-[repeat(7,8px)] gap-y-[3px] leading-2" aria-hidden="true">
						{DAY_LABELS[weekStart].map((d, i) => (
							// biome-ignore lint/suspicious/noArrayIndexKey: seven fixed rows, labels repeat ("")
							<span key={i}>{d}</span>
						))}
					</div>
					<div
						ref={gridRef}
						role="application"
						aria-roledescription="calendar heatmap"
						aria-label={label}
						// biome-ignore lint/a11y/noNoninteractiveTabindex: one tab stop the arrows walk
						tabIndex={0}
						onPointerMove={onPointerMove}
						onPointerLeave={() => setActive(null)}
						onKeyDown={onKeyDown}
						onBlur={() => setActive(null)}
						className={cn(
							"grid grid-flow-col grid-rows-[repeat(7,8px)] auto-cols-[8px] gap-[3px] rounded-[2px]",
							"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
						)}
					>
						{cells}
					</div>
				</div>
			</div>

			{(showLegend || (peakLabel && model.peak)) && (
				<div data-slot="calendar-heatmap-footer" className="flex items-center gap-1">
					{peakLabel && model.peak ? (
						<span
							className="flex-1 truncate"
							title={
								describeParts(model.peak.parts, unit, formatFull) + (suffix ? ` ${suffix}` : "")
							}
						>
							{peakLabel} {formatDay(model.peak.date)}: {describeParts(model.peak.parts, unit)}
						</span>
					) : (
						<span className="flex-1" />
					)}
					{showLegend && (
						<span className="inline-flex items-center gap-1" aria-hidden="true">
							Less
							{LEVELS.map((l) => (
								<i key={l} className={cn("inline-block size-2 rounded-[2px]", levels[l])} />
							))}
							More
						</span>
					)}
				</div>
			)}

			<span className="sr-only" aria-live="polite">
				{keyboard ? tip : ""}
			</span>
			<HeatmapTip grid={gridRef} index={active} text={tip} />
		</div>
	);
}

/** The one floating tooltip, fixed over the hovered or walked-to day. */
function HeatmapTip({
	grid,
	index,
	text,
}: {
	grid: React.RefObject<HTMLDivElement | null>;
	index: number | null;
	text: string;
}) {
	const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
	useLayoutEffect(() => {
		const cell = index === null ? null : grid.current?.children[index];
		if (!cell || !text) {
			setPos(null);
			return;
		}
		const r = cell.getBoundingClientRect();
		setPos({ x: r.left + r.width / 2, y: r.top });
	}, [grid, index, text]);
	if (!pos || !text || typeof document === "undefined") return null;
	return createPortal(
		<div
			data-slot="calendar-heatmap-tooltip"
			role="tooltip"
			className={cn(
				"pointer-events-none fixed z-50 -translate-x-1/2 -translate-y-full whitespace-nowrap px-2 py-1 rounded-sm",
				"bg-bg-elevated text-text-primary border border-border-default shadow-floating",
				"text-xs leading-tight tabular-nums",
			)}
			style={{ left: pos.x, top: pos.y - 6 }}
		>
			{text}
		</div>,
		document.body,
	);
}

export { CalendarHeatmap };
