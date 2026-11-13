import { cva, type VariantProps } from "class-variance-authority";
import { RadioGroup as RadioGroupPrimitive } from "radix-ui";
import * as React from "react";

import { cn } from "../../lib/utils";

// Single choice drawn as a joined row of buttons (`Day | Week | Month`).
// Radix RadioGroup underneath, so it is a radiogroup to assistive tech and
// the keyboard: Tab enters on the picked segment, arrows move the pick, Tab
// leaves (a11y.md §3 RadioGroup). The look is the segmented Tabs list: a
// sunken track with the picked segment raised on a surface pill, so a
// segmented filter and segmented tabs read as one family. The track is the
// height of an input of the same size, so it sits in a form row flush.

const segmentedControlVariants = cva(
	[
		"inline-flex items-stretch gap-0.5 rounded-md p-0.5",
		"bg-bg-sunken border border-border-default",
		"aria-invalid:border-status-danger",
	].join(" "),
	{
		variants: {
			size: {
				sm: "h-6",
				md: "h-8",
				lg: "h-10",
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

const segmentedItemVariants = cva(
	[
		"inline-flex flex-1 items-center justify-center gap-1.5 whitespace-nowrap rounded-sm",
		"font-medium text-text-secondary",
		"cursor-default",
		"transition-colors duration-fast ease-out",
		"hover:text-text-primary",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"disabled:pointer-events-none disabled:opacity-50",
		"data-[state=checked]:bg-bg-surface data-[state=checked]:text-text-primary data-[state=checked]:shadow-raised",
		"[&_svg]:pointer-events-none [&_svg]:shrink-0",
	].join(" "),
	{
		variants: {
			size: {
				sm: "px-2 text-sm [&_svg]:size-3.5",
				md: "px-3 text-base [&_svg]:size-4",
				lg: "px-4 text-lg [&_svg]:size-4",
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

type SegmentedSize = "sm" | "md" | "lg";

const SegmentedSizeContext = React.createContext<SegmentedSize>("md");

export interface SegmentedControlProps
	extends Omit<React.ComponentProps<typeof RadioGroupPrimitive.Root>, "orientation">,
		VariantProps<typeof segmentedControlVariants> {
	invalid?: boolean;
	/** Stretch the track to the width it is given, segments sharing it evenly. */
	fill?: boolean;
}

export function SegmentedControl({
	className,
	size,
	invalid,
	fill,
	...props
}: SegmentedControlProps) {
	return (
		<SegmentedSizeContext.Provider value={size ?? "md"}>
			<RadioGroupPrimitive.Root
				data-slot="segmented-control"
				orientation="horizontal"
				aria-invalid={invalid || undefined}
				className={cn(segmentedControlVariants({ size }), fill && "flex w-full", className)}
				{...props}
			/>
		</SegmentedSizeContext.Provider>
	);
}

export type SegmentedControlItemProps = React.ComponentProps<typeof RadioGroupPrimitive.Item>;

export function SegmentedControlItem({ className, ...props }: SegmentedControlItemProps) {
	const size = React.useContext(SegmentedSizeContext);
	return (
		<RadioGroupPrimitive.Item
			data-slot="segmented-control-item"
			className={cn(segmentedItemVariants({ size }), className)}
			{...props}
		/>
	);
}

export { segmentedControlVariants, segmentedItemVariants };
