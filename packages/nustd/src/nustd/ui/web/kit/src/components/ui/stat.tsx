// Stat primitive.
//
// KPI tile. Compound: Stat / StatLabel / StatValue / StatDelta. Layout is a
// vertical stack by default; consumers can class-override to flip.

import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";

function Stat({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="stat"
			className={cn("flex flex-col gap-1", className)}
			{...props}
		/>
	);
}

function StatLabel({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="stat-label"
			className={cn(
				"font-display text-xs font-medium tracking-[0.02em] text-text-secondary uppercase",
				className,
			)}
			{...props}
		/>
	);
}

function StatValue({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="stat-value"
			className={cn(
				"font-display text-2xl font-semibold tabular-nums text-text-primary leading-none",
				className,
			)}
			{...props}
		/>
	);
}

export interface StatDeltaProps extends React.HTMLAttributes<HTMLDivElement> {
	direction?: "up" | "down" | "flat";
	// direction usually maps up->ok, down->danger; invert=true flips it so a
	// falling metric (e.g. error rate down) reads as ok.
	invert?: boolean;
}

function StatDelta({
	className,
	direction = "flat",
	invert = false,
	children,
	...props
}: StatDeltaProps) {
	const isUp = direction === "up";
	const isDown = direction === "down";
	// Semantic-tone resolution: for a normal metric, up=ok, down=danger. If the
	// consumer marks invert (e.g. error count), swap them so the color reads
	// intuitively.
	const positive = invert ? isDown : isUp;
	const negative = invert ? isUp : isDown;
	const toneClass = positive
		? "text-status-ok"
		: negative
			? "text-status-danger"
			: "text-text-muted";
	const Icon = isUp ? ArrowUp : isDown ? ArrowDown : Minus;
	return (
		<div
			data-slot="stat-delta"
			data-direction={direction}
			className={cn(
				"inline-flex items-center gap-1 text-sm font-medium tabular-nums",
				toneClass,
				className,
			)}
			{...props}
		>
			<Icon aria-hidden="true" className="size-3.5" />
			{children}
		</div>
	);
}

export { Stat, StatLabel, StatValue, StatDelta };
