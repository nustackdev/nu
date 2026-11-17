import type * as React from "react";
import { cn } from "../../lib/utils";

// LevelMeter: how loud a live input is, as a row of short bars that light
// from the left. For a microphone while it records (lib/capture/use-level.ts
// hands the level), or any other live signal in [0, 1].
//
// Bars, not a sliding fill: a lit bar is on or off, so nothing animates and
// reduced motion needs no special case. Live is Starlight (`accent-2`), the
// unlit bars sit at the border step. The meter is decoration: the state it
// belongs to is said in words beside it, so it is hidden from assistive tech.

export interface LevelMeterProps extends Omit<React.ComponentProps<"span">, "children"> {
	/** The level in [0, 1]. */
	level: number;
	/** How many bars. Default 12. */
	bars?: number;
	/** Dims the meter (a paused input still shows where it was). */
	quiet?: boolean;
}

export function LevelMeter({
	level,
	bars = 12,
	quiet = false,
	className,
	...props
}: LevelMeterProps) {
	const lit = Math.round(Math.min(1, Math.max(0, Number.isFinite(level) ? level : 0)) * bars);
	return (
		<span
			data-slot="level-meter"
			aria-hidden
			className={cn("flex h-3 items-center gap-0.5", quiet && "opacity-50", className)}
			{...props}
		>
			{Array.from({ length: bars }, (_, i) => (
				<span
					// biome-ignore lint/suspicious/noArrayIndexKey: a bar is its position.
					key={i}
					data-lit={i < lit || undefined}
					className={cn(
						"h-full w-1 shrink-0 rounded-full",
						i < lit ? "bg-accent-2" : "bg-border-default",
					)}
				/>
			))}
		</span>
	);
}
