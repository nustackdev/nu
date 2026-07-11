// Image primitive.
//
// Thin <img> wrapper with radius + fit + aspect ratio + loading placeholder.
// Alt is required in the prop type per a11y.md §7.

import type * as React from "react";

import { cn } from "../../lib/utils";

const RADIUS_CLASS = {
	none: "rounded-none",
	sm: "rounded-sm",
	md: "rounded-md",
	lg: "rounded-lg",
} as const;

const FIT_CLASS = {
	cover: "object-cover",
	contain: "object-contain",
	fill: "object-fill",
	none: "object-none",
	"scale-down": "object-scale-down",
} as const;

export interface ImageProps
	extends Omit<React.ImgHTMLAttributes<HTMLImageElement>, "alt"> {
	alt: string;
	radius?: keyof typeof RADIUS_CLASS;
	fit?: keyof typeof FIT_CLASS;
	// aspectRatio accepts a CSS aspect ratio string (e.g. "16 / 9", "1 / 1")
	// so callers can preserve layout while the image loads.
	aspectRatio?: string;
}

function Image({
	className,
	alt,
	radius = "md",
	fit = "cover",
	aspectRatio,
	style,
	...props
}: ImageProps) {
	return (
		<img
			data-slot="image"
			alt={alt}
			className={cn(
				"block max-w-full bg-bg-sunken",
				RADIUS_CLASS[radius],
				FIT_CLASS[fit],
				className,
			)}
			style={{
				aspectRatio,
				...style,
			}}
			{...props}
		/>
	);
}

export { Image };
