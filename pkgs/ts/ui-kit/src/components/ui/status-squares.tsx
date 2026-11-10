// StatusSquares primitive. A strip of small status squares, one per item.
//
// Takes counts per tone, not a list of items, so a thousand items cost the
// same as ten. Draws at most `maxItems` squares (default 10). Tones fill in
// severity order, danger first and empty last, so a problem never hides past
// the cap. Past the cap an ellipsis follows, then the full count: the strip
// never drops items without saying how many there are.
//
// Tones are the StatusDot ones plus `empty`, an outlined square for an item
// that is there and doing nothing (idle). The strip is a named image: the
// label spells every tone's count, worded through `labels` when given.

import type * as React from "react";

import { formatCount, formatFullCount } from "../../lib/count";
import { cn } from "../../lib/utils";

export const STATUS_SQUARE_TONES = ["danger", "warn", "info", "ok", "neutral", "empty"] as const;

export type StatusSquareTone = (typeof STATUS_SQUARE_TONES)[number];

export type StatusSquareCounts = Partial<Record<StatusSquareTone, number>>;

/** When the full count shows: only past the cap, always, or never. */
export type StatusSquaresTotal = "overflow" | "always" | "never";

const SQUARE_TONE_CLASS: Record<StatusSquareTone, string> = {
	danger: "bg-status-danger",
	warn: "bg-status-warn",
	info: "bg-status-info",
	ok: "bg-status-ok",
	neutral: "bg-text-secondary/40",
	empty: "border border-border-strong",
};

function cleanCount(n: number | undefined): number {
	return typeof n === "number" && Number.isFinite(n) && n > 0 ? Math.floor(n) : 0;
}

/** The tones to draw, in severity order, at most `cap` of them. */
export function squaresFor(counts: StatusSquareCounts, cap: number): StatusSquareTone[] {
	const out: StatusSquareTone[] = [];
	const limit = Math.max(0, Math.floor(cap));
	for (const tone of STATUS_SQUARE_TONES) {
		const n = cleanCount(counts[tone]);
		for (let i = 0; i < n && out.length < limit; i++) out.push(tone);
		if (out.length >= limit) break;
	}
	return out;
}

export interface StatusSquaresProps extends Omit<React.ComponentProps<"div">, "children"> {
	counts: StatusSquareCounts;
	/** Most squares drawn. Past it, an ellipsis and the full count. */
	maxItems?: number;
	/** Words per tone for the accessible label ("failed", "running"). */
	labels?: Partial<Record<StatusSquareTone, string>>;
	total?: StatusSquaresTotal;
}

export function StatusSquares({
	counts,
	maxItems = 10,
	labels,
	total = "overflow",
	className,
	...props
}: StatusSquaresProps) {
	const shown = squaresFor(counts, maxItems);
	const sum = STATUS_SQUARE_TONES.reduce((acc, t) => acc + cleanCount(counts[t]), 0);
	const over = sum > shown.length;
	const showTotal = total === "always" || (total === "overflow" && over);
	const label =
		STATUS_SQUARE_TONES.filter((t) => cleanCount(counts[t]) > 0)
			.map((t) => `${formatFullCount(cleanCount(counts[t]))} ${labels?.[t] ?? t}`)
			.join(", ") || "none";

	return (
		<div
			data-slot="status-squares"
			role="img"
			aria-label={label}
			title={label}
			className={cn("inline-flex items-center gap-[3px]", className)}
			{...props}
		>
			{shown.map((tone, i) => (
				<span
					// biome-ignore lint/suspicious/noArrayIndexKey: squares are positions, not identities
					key={i}
					data-tone={tone}
					className={cn("inline-block size-[11px] shrink-0 rounded-[2px]", SQUARE_TONE_CLASS[tone])}
				/>
			))}
			{over && (
				<span
					data-slot="status-squares-more"
					className="ml-[3px] text-xs leading-none text-text-muted"
				>
					…
				</span>
			)}
			{showTotal && (
				<span
					data-slot="status-squares-total"
					className="ml-1.5 text-xs leading-none tabular-nums text-text-secondary first:ml-0"
				>
					{formatCount(sum)}
				</span>
			)}
		</div>
	);
}
