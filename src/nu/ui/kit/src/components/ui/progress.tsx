// Progress primitive.
//
// Radix Progress with kit variants. Indeterminate is opt-in by passing
// value={null|undefined}; Radix drops aria-valuenow accordingly.

import { cva, type VariantProps } from "class-variance-authority";
import { Progress as ProgressPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const progressVariants = cva("relative w-full overflow-hidden rounded-full bg-bg-sunken", {
	variants: {
		size: {
			sm: "h-1",
			md: "h-1.5",
			lg: "h-2",
		},
		tone: {
			default: "",
			info: "",
			danger: "",
			warn: "",
			ok: "",
		},
	},
	defaultVariants: {
		size: "md",
		tone: "default",
	},
});

const INDICATOR_TONE_CLASS: Record<
	NonNullable<VariantProps<typeof progressVariants>["tone"]>,
	string
> = {
	default: "bg-accent",
	info: "bg-status-info",
	danger: "bg-status-danger",
	warn: "bg-status-warn",
	ok: "bg-status-ok",
};

export interface ProgressProps
	extends React.ComponentProps<typeof ProgressPrimitive.Root>,
		VariantProps<typeof progressVariants> {}

function Progress({ className, size, tone, value, max, ...props }: ProgressProps) {
	const effectiveTone = tone ?? "default";
	const pct = typeof value === "number" ? (value / (max ?? 100)) * 100 : 0;
	const indeterminate = value == null;
	return (
		<ProgressPrimitive.Root
			data-slot="progress"
			data-indeterminate={indeterminate || undefined}
			value={value}
			max={max}
			className={cn(progressVariants({ size, tone }), className)}
			{...props}
		>
			<ProgressPrimitive.Indicator
				data-slot="progress-indicator"
				// Value change animates locally; indeterminate loops via keyframes.
				className={cn(
					"h-full w-full flex-1 transition-transform ease-linear",
					"duration-[300ms]",
					INDICATOR_TONE_CLASS[effectiveTone],
				)}
				style={{
					transform: indeterminate ? undefined : `translateX(-${100 - pct}%)`,
				}}
			/>
		</ProgressPrimitive.Root>
	);
}

export { Progress, progressVariants };
