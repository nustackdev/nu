// Sheet primitive: edge-anchored slide-in drawer built on Radix Dialog.
// Design refs:
//   primitives.md    §Sheet (parts, sides, width / height)
//   palette.md       backgrounds, borders
//   space-radius.md  §Density Sheet (pad 20, radius `xl`)
//   motion.md        §3 Sheet (`duration-slow` slide, no content fade)
//   a11y.md          §3 Sheet (same focus trap as Dialog)
//
// Reuses Radix Dialog: same portal, backdrop, focus trap, Esc semantics.
// The variance is chrome: side prop drives slide direction and edge-fit.

import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import { Dialog as SheetPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";
import { lengthCss } from "./dialog";
import { IconButton } from "./icon-button";

// Fixed edge-anchored positioning per side + slide-in/out per side.
const sheetContentVariants = cva(
	[
		"fixed z-50 flex flex-col gap-4 bg-bg-elevated border-border-default text-text-primary shadow-modal",
		"p-5",
		"data-[state=open]:animate-in data-[state=closed]:animate-out",
		"data-[state=open]:duration-slow data-[state=closed]:duration-slow",
		"data-[state=open]:ease-out data-[state=closed]:ease-in",
	].join(" "),
	{
		variants: {
			side: {
				top: [
					"inset-x-0 top-0 border-b rounded-b-xl",
					"data-[state=open]:slide-in-from-top data-[state=closed]:slide-out-to-top",
				].join(" "),
				bottom: [
					"inset-x-0 bottom-0 border-t rounded-t-xl",
					"data-[state=open]:slide-in-from-bottom data-[state=closed]:slide-out-to-bottom",
				].join(" "),
				left: [
					"inset-y-0 left-0 border-r rounded-r-xl",
					"data-[state=open]:slide-in-from-left data-[state=closed]:slide-out-to-left",
				].join(" "),
				right: [
					"inset-y-0 right-0 border-l rounded-l-xl",
					"data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right",
				].join(" "),
			},
		},
		compoundVariants: [
			// left / right sheets: 440px wide unless `width` says, full height.
			{ side: ["left", "right"], class: "h-full w-[27.5rem]" },
			// top / bottom sheets: 320px tall unless `height` says, full width.
			{ side: ["top", "bottom"], class: "w-full h-80" },
		],
		defaultVariants: {
			side: "right",
		},
	},
);

function Sheet({ ...props }: React.ComponentProps<typeof SheetPrimitive.Root>) {
	return <SheetPrimitive.Root data-slot="sheet" {...props} />;
}

function SheetTrigger({ ...props }: React.ComponentProps<typeof SheetPrimitive.Trigger>) {
	return <SheetPrimitive.Trigger data-slot="sheet-trigger" {...props} />;
}

function SheetClose({ ...props }: React.ComponentProps<typeof SheetPrimitive.Close>) {
	return <SheetPrimitive.Close data-slot="sheet-close" {...props} />;
}

function SheetPortal({ ...props }: React.ComponentProps<typeof SheetPrimitive.Portal>) {
	return <SheetPrimitive.Portal data-slot="sheet-portal" {...props} />;
}

function SheetOverlay({
	className,
	...props
}: React.ComponentProps<typeof SheetPrimitive.Overlay>) {
	return (
		<SheetPrimitive.Overlay
			data-slot="sheet-overlay"
			className={cn(
				"fixed inset-0 z-50 bg-bg-overlay",
				"data-[state=open]:animate-in data-[state=closed]:animate-out",
				"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
				"data-[state=open]:duration-slow data-[state=closed]:duration-slow",
				"data-[state=open]:ease-out data-[state=closed]:ease-in",
				className,
			)}
			{...props}
		/>
	);
}

export interface SheetContentProps
	extends React.ComponentProps<typeof SheetPrimitive.Content>,
		VariantProps<typeof sheetContentVariants> {
	/** A left or right sheet's width (440px unless set): px, or a CSS length. */
	width?: number | string;
	/** A top or bottom sheet's height (320px unless set): px, or a CSS length. */
	height?: number | string;
	showClose?: boolean;
}

function SheetContent({
	className,
	side,
	width,
	height,
	style,
	children,
	showClose = true,
	...props
}: SheetContentProps) {
	const size: React.CSSProperties = {};
	if (width !== undefined) size.width = lengthCss(width);
	if (height !== undefined) size.height = lengthCss(height);
	return (
		<SheetPortal>
			<SheetOverlay />
			<SheetPrimitive.Content
				data-slot="sheet-content"
				className={cn(sheetContentVariants({ side }), className)}
				style={{ ...size, ...style }}
				{...props}
			>
				{children}
				{showClose && (
					// A kit IconButton, like every other icon-only control.
					<SheetPrimitive.Close asChild>
						<IconButton
							data-slot="sheet-close-icon"
							variant="ghost"
							size="sm"
							ring="inset"
							aria-label="Close"
							className="absolute right-4 top-4"
						>
							<X />
						</IconButton>
					</SheetPrimitive.Close>
				)}
			</SheetPrimitive.Content>
		</SheetPortal>
	);
}

function SheetHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="sheet-header"
			className={cn("flex flex-col gap-1.5 text-left", className)}
			{...props}
		/>
	);
}

function SheetFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="sheet-footer"
			className={cn("mt-auto flex flex-col gap-2 sm:flex-row sm:justify-end", className)}
			{...props}
		/>
	);
}

function SheetTitle({ className, ...props }: React.ComponentProps<typeof SheetPrimitive.Title>) {
	return (
		<SheetPrimitive.Title
			data-slot="sheet-title"
			className={cn("text-2xl font-semibold leading-tight text-text-primary", className)}
			{...props}
		/>
	);
}

function SheetDescription({
	className,
	...props
}: React.ComponentProps<typeof SheetPrimitive.Description>) {
	return (
		<SheetPrimitive.Description
			data-slot="sheet-description"
			className={cn("text-sm text-text-secondary", className)}
			{...props}
		/>
	);
}

export {
	Sheet,
	SheetClose,
	SheetContent,
	SheetDescription,
	SheetFooter,
	SheetHeader,
	SheetOverlay,
	SheetPortal,
	SheetTitle,
	SheetTrigger,
	sheetContentVariants,
};
