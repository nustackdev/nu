// Gauge primitive.
//
// Semicircle dial (180deg arc) with a value indicator + numeric label. Sized
// via cva so callers pick a fixed footprint; SVG scales inside the box.

import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "../../lib/utils";

const gaugeVariants = cva("inline-flex flex-col items-center justify-center", {
	variants: {
		size: {
			sm: "size-16",
			md: "size-24",
			lg: "size-32",
		},
	},
	defaultVariants: {
		size: "md",
	},
});

const ARC_TONE_CLASS = {
	accent: "text-accent",
	info: "text-status-info",
	danger: "text-status-danger",
	warn: "text-status-warn",
	ok: "text-status-ok",
	accent2: "text-accent-2",
} as const;

const LABEL_SIZE_CLASS = {
	sm: "text-xs",
	md: "text-sm",
	lg: "text-lg",
} as const;

export interface GaugeProps
	extends Omit<React.HTMLAttributes<HTMLDivElement>, "children">,
		VariantProps<typeof gaugeVariants> {
	value: number;
	min?: number;
	max?: number;
	tone?: keyof typeof ARC_TONE_CLASS;
	label?: string;
	formatValue?: (value: number) => string;
}

function Gauge({
	className,
	size,
	value,
	min = 0,
	max = 100,
	tone = "accent",
	label,
	formatValue,
	...props
}: GaugeProps) {
	const clamped = Math.max(min, Math.min(max, value));
	const ratio = max === min ? 0 : (clamped - min) / (max - min);

	// Geometry: viewBox 100x60 hosts a semicircle of radius 40 centred at (50, 50).
	// Path length ≈ pi * r ≈ 125.66. We drive strokeDasharray/offset to reveal
	// the arc proportional to the value.
	const arcLength = Math.PI * 40;
	const offset = arcLength * (1 - ratio);

	const effectiveSize: NonNullable<VariantProps<typeof gaugeVariants>["size"]> =
		size ?? "md";
	const display = formatValue ? formatValue(clamped) : String(Math.round(clamped));

	return (
		<div
			role="meter"
			aria-valuenow={clamped}
			aria-valuemin={min}
			aria-valuemax={max}
			aria-label={label}
			data-slot="gauge"
			className={cn(gaugeVariants({ size: effectiveSize }), className)}
			{...props}
		>
			<svg
				viewBox="0 0 100 60"
				className="w-full h-auto"
				fill="none"
				aria-hidden="true"
			>
				{/* Track arc: bg-sunken tone */}
				<path
					d="M 10 50 A 40 40 0 0 1 90 50"
					className="stroke-bg-sunken"
					strokeWidth="8"
					strokeLinecap="round"
				/>
				{/* Value arc: tone-driven, animated with duration-base */}
				<path
					d="M 10 50 A 40 40 0 0 1 90 50"
					className={cn(
						ARC_TONE_CLASS[tone],
						"transition-[stroke-dashoffset] duration-base ease-out",
					)}
					stroke="currentColor"
					strokeWidth="8"
					strokeLinecap="round"
					strokeDasharray={arcLength}
					strokeDashoffset={offset}
				/>
			</svg>
			<span
				className={cn(
					"-mt-3 font-display font-semibold tabular-nums text-text-primary",
					LABEL_SIZE_CLASS[effectiveSize],
				)}
			>
				{display}
			</span>
		</div>
	);
}

export { Gauge, gaugeVariants };
