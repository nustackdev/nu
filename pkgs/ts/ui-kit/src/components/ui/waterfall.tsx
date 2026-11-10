// Waterfall primitive. Spans on one shared time axis, like a trace view.
//
// Each span is a row: its label on the left, indented by depth, and a bar on
// the track at its start and end, with the duration beside it. Nesting comes
// from `parent`; without it the spans read as a sequence. Layout, the window
// and the axis live in waterfall-model.ts.
//
// Native DOM, no chart library: bars are absolutely placed by percentage, so
// a row costs a few elements and the cap keeps the count bounded. Past
// `maxRows` (default 50) a last row says how many spans are left and how many
// of those failed: the waterfall never drops a span without a number.
//
// Tone is the StatusDot set. A finished ok span is a half tone and a
// running one solid with a live edge, so failures and work in flight are
// what stand out. Color never carries the tone alone: every bar names its
// span, state and duration to assistive tech, and the hover hint says it in
// words.
//
// `onSelect` makes each row a button; `selected` marks one with the press
// wash (palette.md states). Rows are controls, so the arrow cursor
// (cursor.md).

import type * as React from "react";

import { formatCount } from "../../lib/count";
import { cn } from "../../lib/utils";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";
import {
	formatSpanTime,
	isRunning,
	spanEnd,
	toneOf,
	type WaterfallSpan,
	type WaterfallTone,
	waterfallRows,
	waterfallTicks,
	waterfallWindow,
} from "./waterfall-model";

const BAR_TONE_CLASS: Record<WaterfallTone, string> = {
	neutral: "bg-text-secondary/40",
	info: "bg-status-info",
	ok: "bg-status-ok/50",
	warn: "bg-status-warn",
	danger: "bg-status-danger",
};

const RUNNING_TONE_CLASS: Record<WaterfallTone, string> = {
	...BAR_TONE_CLASS,
	ok: "bg-status-ok",
};

const TONE_WORD: Record<WaterfallTone, string> = {
	neutral: "",
	info: "info",
	ok: "ok",
	warn: "warning",
	danger: "failed",
};

const INDENT_PX = 12;

export interface WaterfallProps
	extends Omit<React.HTMLAttributes<HTMLDivElement>, "children" | "onSelect"> {
	spans: readonly WaterfallSpan[];
	/** Window start in ms. Default: the earliest span start. */
	start?: number;
	/** Window end in ms. Default: the latest span end, or `now`. */
	end?: number;
	/** Where running spans stop, in ms. Default: the window end. */
	now?: number;
	/** Most rows drawn. Past it, one row with the rest counted. */
	maxRows?: number;
	/** Label column width in px. */
	labelWidth?: number;
	/** Formats axis offsets and durations, in ms. */
	formatTime?: (ms: number) => string;
	selected?: string | null;
	onSelect?: (span: WaterfallSpan) => void;
}

function clamp(n: number): number {
	return Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
}

function pct(n: number): string {
	return `${clamp(n).toFixed(4)}%`;
}

function Waterfall({
	spans,
	start,
	end,
	now,
	maxRows = 50,
	labelWidth = 200,
	formatTime = formatSpanTime,
	selected,
	onSelect,
	className,
	style,
	...props
}: WaterfallProps) {
	const win = waterfallWindow(spans, { start, end, now });
	const range = win.end - win.start;
	const at = (t: number) => ((t - win.start) / range) * 100;
	const ticks = waterfallTicks(range);
	const { rows, hidden, hiddenDanger } = waterfallRows(spans, maxRows);
	const cols = { gridTemplateColumns: `${labelWidth}px minmax(0, 1fr)` };

	return (
		<TooltipProvider>
			<div
				data-slot="waterfall"
				className={cn("flex min-w-0 flex-col font-display text-xs", className)}
				style={style}
				{...props}
			>
				<div data-slot="waterfall-axis" className="grid h-6 items-end gap-3" style={cols}>
					<span />
					<div className="relative h-full" aria-hidden="true">
						{ticks.map((t, i) => {
							const x = (t / range) * 100;
							const last = i === ticks.length - 1 && x > 90;
							return (
								<span
									key={t}
									className={cn(
										"absolute bottom-1 whitespace-nowrap text-text-muted tabular-nums",
										last ? "-translate-x-full" : i > 0 && "-translate-x-1/2",
									)}
									style={{ left: pct(x) }}
								>
									{formatTime(t)}
								</span>
							);
						})}
					</div>
				</div>

				<div className="relative">
					<div
						className="pointer-events-none absolute inset-y-0 right-0 grid gap-3"
						style={{ ...cols, left: 0 }}
						aria-hidden="true"
					>
						<span />
						<div className="relative">
							{ticks.map((t) => (
								<span
									key={t}
									className="absolute inset-y-0 border-l border-border-subtle"
									style={{ left: pct((t / range) * 100) }}
								/>
							))}
						</div>
					</div>

					<ul data-slot="waterfall-rows" className="relative">
						{rows.map(({ span, depth }) => {
							const tone = toneOf(span);
							const running = isRunning(span);
							const stop = spanEnd(span, win.end, now);
							const x0 = clamp(at(span.start));
							const x1 = Math.max(x0, clamp(at(stop)));
							const dur = formatTime(stop - span.start);
							const offset = formatTime(span.start - win.start);
							const words = [
								span.label,
								running ? "running" : TONE_WORD[tone],
								running ? `${dur} so far` : dur,
								`at ${offset}`,
							]
								.filter(Boolean)
								.join(", ");
							// Duration after the bar, else before it. A bar too wide for
							// either puts it at the end of its label cell: the text is
							// taller than the bar, so it never sits on top of it.
							const durInLabel = x1 >= 75 && x0 <= 25;
							const durAt: React.CSSProperties =
								x1 < 75
									? { left: `calc(${pct(x1)} + 6px)` }
									: { right: `calc(${pct(100 - x0)} + 6px)` };
							const isSel = selected != null && selected === span.id;
							const label = (
								<span
									className="flex min-w-0 items-center"
									style={{ paddingLeft: depth * INDENT_PX }}
								>
									<span className="truncate text-text-secondary">{span.label}</span>
									{durInLabel ? (
										<span
											aria-hidden="true"
											className="ml-auto shrink-0 pl-2 whitespace-nowrap text-text-muted tabular-nums"
										>
											{dur}
										</span>
									) : null}
								</span>
							);
							const track = (
								<span className="relative block h-6">
									<Tooltip>
										<TooltipTrigger asChild>
											<span
												data-slot="waterfall-bar"
												data-tone={tone}
												data-running={running || undefined}
												role="img"
												aria-label={words}
												className={cn(
													"absolute top-1/2 h-2 min-w-0.5 -translate-y-1/2 rounded-sm",
													(running ? RUNNING_TONE_CLASS : BAR_TONE_CLASS)[tone],
												)}
												style={{ left: pct(x0), width: pct(x1 - x0) }}
											>
												{running ? (
													<span
														className={cn(
															"absolute -right-0.5 top-1/2 h-3 w-1 -translate-y-1/2 rounded-sm animate-pulse",
															RUNNING_TONE_CLASS[tone],
														)}
													/>
												) : null}
											</span>
										</TooltipTrigger>
										<TooltipContent side="top">
											<span className="block font-medium">{span.label}</span>
											<span className="block text-text-secondary tabular-nums">
												{[
													running ? "running" : TONE_WORD[tone],
													running ? `${dur} so far` : dur,
													`at +${offset}`,
												]
													.filter(Boolean)
													.join(" · ")}
											</span>
											{span.detail ? (
												<span className="block text-text-secondary">{span.detail}</span>
											) : null}
										</TooltipContent>
									</Tooltip>
									{durInLabel ? null : (
										<span
											aria-hidden="true"
											className="absolute top-1/2 -translate-y-1/2 whitespace-nowrap text-text-muted tabular-nums"
											style={durAt}
										>
											{dur}
										</span>
									)}
								</span>
							);
							const rowClass = cn(
								"grid h-6 w-full items-center gap-3 rounded-sm px-0 text-left",
								isSel && "bg-bg-press",
							);
							return (
								<li key={span.id} data-slot="waterfall-row" data-depth={depth}>
									{onSelect ? (
										<button
											type="button"
											aria-pressed={isSel}
											aria-label={words}
											className={cn(
												rowClass,
												!isSel && "hover:bg-bg-hover active:bg-bg-press",
												"cursor-default focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
											)}
											style={cols}
											onClick={() => onSelect(span)}
										>
											{label}
											{track}
										</button>
									) : (
										<div className={rowClass} style={cols}>
											{label}
											{track}
										</div>
									)}
								</li>
							);
						})}
					</ul>
				</div>

				{hidden > 0 ? (
					<div
						data-slot="waterfall-more"
						className="grid h-7 items-center gap-3 text-text-muted"
						style={cols}
					>
						<span>
							<span className="font-medium text-text-secondary tabular-nums">
								+{formatCount(hidden)}
							</span>{" "}
							more {hidden === 1 ? "span" : "spans"}
							{hiddenDanger > 0 ? (
								<span className="text-status-danger tabular-nums">
									{" "}
									· {formatCount(hiddenDanger)} failed
								</span>
							) : null}
						</span>
						<span />
					</div>
				) : null}
			</div>
		</TooltipProvider>
	);
}

export type { WaterfallSpan, WaterfallTone } from "./waterfall-model";
export { Waterfall };
