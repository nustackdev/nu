// Avatar primitive.
//
// Radix Avatar. Fallback paints over bg-bg-sunken with text-text-secondary
// initials or a lucide User glyph if consumer opts in.

import { cva, type VariantProps } from "class-variance-authority";
import { Avatar as AvatarPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const avatarVariants = cva(
	"relative inline-flex shrink-0 overflow-hidden rounded-full bg-bg-sunken",
	{
		variants: {
			size: {
				sm: "size-6", // 24px
				md: "size-8", // 32px
				lg: "size-10", // 40px
				xl: "size-12", // 48px
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

export interface AvatarProps
	extends React.ComponentProps<typeof AvatarPrimitive.Root>,
		VariantProps<typeof avatarVariants> {}

function Avatar({ className, size, ...props }: AvatarProps) {
	return (
		<AvatarPrimitive.Root
			data-slot="avatar"
			className={cn(avatarVariants({ size }), className)}
			{...props}
		/>
	);
}

function AvatarImage({
	className,
	...props
}: React.ComponentProps<typeof AvatarPrimitive.Image>) {
	return (
		<AvatarPrimitive.Image
			data-slot="avatar-image"
			className={cn("aspect-square size-full object-cover", className)}
			{...props}
		/>
	);
}

function AvatarFallback({
	className,
	...props
}: React.ComponentProps<typeof AvatarPrimitive.Fallback>) {
	return (
		<AvatarPrimitive.Fallback
			data-slot="avatar-fallback"
			className={cn(
				"flex size-full items-center justify-center bg-bg-sunken",
				"font-display text-xs font-medium text-text-secondary uppercase tracking-[0.02em]",
				className,
			)}
			{...props}
		/>
	);
}

export { Avatar, AvatarImage, AvatarFallback };
