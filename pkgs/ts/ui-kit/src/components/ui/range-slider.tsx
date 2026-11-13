// RangeSlider: the kit Slider with two thumbs, a low and a high, plus an
// optional readout ("20 - 80") and marks under the track.
//
// The root is a `role="group"`: name it with `aria-labelledby` (or
// `aria-label`), and each thumb carries its own name from `thumbLabels`
// ("Minimum", "Maximum" by default), so a screen reader hears the group, then
// which end it is on. Keys are the kit Slider's (a11y.md §3 Slider); the
// thumbs cannot cross.
//
// Marks sit where the thumb centre sits at that value: Radix keeps a thumb
// inside the track at the ends, so a mark is nudged in by the same amount.

import * as React from "react";

import { cn } from "../../lib/utils";
import { Slider, type SliderProps } from "./slider";

type Size = "sm" | "md" | "lg";
export type SliderRange = [number, number];
export type SliderMark = { value: number; label?: string };

// The thumb widths in px, the kit Slider's `size-3`, `size-3.5`, `size-[18px]`.
const THUMB_PX = { sm: 12, md: 14, lg: 18 } as const;

/** Decimal places in `step`, so 0.1 steps read 0.3 and not 0.30000000000000004. */
export function stepDecimals(step: number): number {
	const s = String(step);
	const e = /e-(\d+)$/.exec(s);
	if (e) return Number(e[1]);
	const dot = s.indexOf(".");
	return dot < 0 ? 0 : s.length - dot - 1;
}

export interface RangeSliderProps
	extends Omit<React.ComponentProps<"div">, "defaultValue" | "onChange" | "dir"> {
	value?: SliderRange;
	defaultValue?: SliderRange;
	/** Every move of a thumb. */
	onValueChange?: (value: SliderRange) => void;
	/** A release, or an arrow key. */
	onValueCommit?: (value: SliderRange) => void;
	min?: number;
	max?: number;
	step?: number;
	size?: Size;
	disabled?: boolean;
	/** The two thumbs' accessible names, low then high. */
	thumbLabels?: [string, string];
	/** Props for both thumbs (aria-describedby, aria-invalid, autofocus). */
	thumbProps?: SliderProps["thumbProps"];
	/** Labelled points under the track. */
	marks?: SliderMark[];
	/** How a value reads in the readout and on a mark without a label. */
	formatValue?: (value: number) => string;
	/** Draw "low - high" at the end of the row. */
	showValue?: boolean;
}

export function RangeSlider({
	value,
	defaultValue,
	onValueChange,
	onValueCommit,
	min = 0,
	max = 100,
	step = 1,
	size = "md",
	disabled,
	thumbLabels = ["Minimum", "Maximum"],
	thumbProps,
	marks,
	formatValue,
	showValue = true,
	className,
	...props
}: RangeSliderProps) {
	const decimals = stepDecimals(step);
	const fmt = formatValue ?? ((n: number) => n.toFixed(decimals));
	const [own, setOwn] = React.useState<SliderRange>(defaultValue ?? [min, max]);
	const shown = value ?? own;
	const span = max - min || 1;
	const thumb = THUMB_PX[size];
	return (
		// biome-ignore lint/a11y/useSemanticElements: a group named by a label elsewhere, not a form section with a legend.
		<div
			role="group"
			data-slot="range-slider"
			data-disabled={disabled || undefined}
			className={cn("flex w-full flex-col gap-1", className)}
			{...props}
		>
			<div className="flex items-center gap-3">
				<div className="relative flex-1">
					<Slider
						value={shown}
						min={min}
						max={max}
						step={step}
						size={size}
						disabled={disabled}
						minStepsBetweenThumbs={0}
						thumbProps={thumbProps}
						thumbLabels={thumbLabels}
						onValueChange={(v) => {
							const next: SliderRange = [v[0] ?? min, v[1] ?? max];
							if (value === undefined) setOwn(next);
							onValueChange?.(next);
						}}
						onValueCommit={(v) => onValueCommit?.([v[0] ?? min, v[1] ?? max])}
					/>
					{marks && marks.length > 0 && (
						<div
							data-slot="range-slider-marks"
							aria-hidden
							className={cn("relative mt-1 h-4", disabled && "opacity-50")}
						>
							{marks.map((m) => {
								const p = Math.min(1, Math.max(0, (m.value - min) / span));
								return (
									<span
										key={m.value}
										className="absolute top-0 -translate-x-1/2 whitespace-nowrap font-mono text-xs text-text-muted tabular-nums"
										style={{ left: `calc(${p * 100}% + ${(0.5 - p) * thumb}px)` }}
									>
										{m.label ?? fmt(m.value)}
									</span>
								);
							})}
						</div>
					)}
				</div>
				{showValue && (
					<span
						data-slot="range-slider-value"
						className={cn(
							"shrink-0 self-start font-mono text-sm text-text-primary tabular-nums leading-5",
							disabled && "opacity-50",
						)}
					>
						{fmt(shown[0])} - {fmt(shown[1])}
					</span>
				)}
			</div>
		</div>
	);
}
