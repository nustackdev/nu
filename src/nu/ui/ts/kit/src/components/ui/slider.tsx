import { cva, type VariantProps } from "class-variance-authority";
import { Slider as SliderPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const sliderVariants = cva(
	[
		"relative flex touch-none select-none items-center",
		"data-[orientation=horizontal]:w-full data-[orientation=horizontal]:h-5",
		"data-[orientation=vertical]:h-full data-[orientation=vertical]:w-5 data-[orientation=vertical]:flex-col",
		"disabled:opacity-50 disabled:pointer-events-none",
	].join(" "),
	{
		variants: {
			size: {
				sm: "",
				md: "",
				lg: "",
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

const sliderTrackSizes = {
	sm: "data-[orientation=horizontal]:h-[3px] data-[orientation=vertical]:w-[3px]",
	md: "data-[orientation=horizontal]:h-1 data-[orientation=vertical]:w-1",
	lg: "data-[orientation=horizontal]:h-[5px] data-[orientation=vertical]:w-[5px]",
} as const;

const sliderThumbSizes = {
	sm: "size-3",
	md: "size-3.5",
	lg: "size-[18px]",
} as const;

export interface SliderProps
	extends Omit<React.ComponentProps<typeof SliderPrimitive.Root>, "size">,
		VariantProps<typeof sliderVariants> {}

export function Slider({
	className,
	size = "md",
	defaultValue,
	value,
	min = 0,
	max = 100,
	...props
}: SliderProps) {
	// Thumb count comes from the initial value shape; a single-thumb slider
	// still renders one thumb even when neither prop is passed.
	const values = value ?? defaultValue ?? [min];
	return (
		<SliderPrimitive.Root
			data-slot="slider"
			className={cn(sliderVariants({ size }), className)}
			defaultValue={defaultValue}
			value={value}
			min={min}
			max={max}
			{...props}
		>
			<SliderPrimitive.Track
				data-slot="slider-track"
				className={cn(
					"relative grow overflow-hidden rounded-full bg-bg-sunken",
					sliderTrackSizes[size ?? "md"],
				)}
			>
				<SliderPrimitive.Range
					data-slot="slider-range"
					className={cn(
						"absolute bg-accent",
						"data-[orientation=horizontal]:h-full data-[orientation=vertical]:w-full",
					)}
				/>
			</SliderPrimitive.Track>
			{values.map((_, i) => (
				<SliderPrimitive.Thumb
					// biome-ignore lint/suspicious/noArrayIndexKey: thumb count is fixed.
					key={i}
					data-slot="slider-thumb"
					className={cn(
						"block shrink-0 rounded-full bg-bg-surface border-2 border-border-strong",
						"cursor-pointer",
						"transition-transform duration-fast ease-out",
						"hover:border-accent",
						"data-[state=active]:bg-accent data-[state=active]:border-accent data-[state=active]:scale-110",
						"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
						"disabled:pointer-events-none",
						sliderThumbSizes[size ?? "md"],
					)}
				/>
			))}
		</SliderPrimitive.Root>
	);
}

export { sliderVariants };
