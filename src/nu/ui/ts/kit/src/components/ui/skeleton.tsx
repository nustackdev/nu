// Skeleton primitive.
//
// Static placeholder shape; the pulse is Tailwind's animate-pulse, killed
// automatically by prefers-reduced-motion via the global override in index.css.

import type * as React from "react";

import { cn } from "../../lib/utils";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
	shape?: "rect" | "text" | "circle";
}

function Skeleton({ className, shape = "rect", ...props }: SkeletonProps) {
	const shapeClass =
		shape === "circle"
			? "rounded-full aspect-square"
			: shape === "text"
				? "rounded-sm h-4"
				: "rounded-md";
	return (
		<div
			data-slot="skeleton"
			aria-hidden="true"
			className={cn("animate-pulse bg-bg-sunken", shapeClass, className)}
			{...props}
		/>
	);
}

export { Skeleton };
