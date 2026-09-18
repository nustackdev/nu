// Sheet primitive: edge-anchored slide-in drawer built on Radix Dialog.
// Design refs:
//   primitives.md    §Sheet (parts, sides, sizes)
//   palette.md       §2.1 backgrounds, §2.3 borders
//   space-radius.md  §Density Sheet (pad 20, radius `xl`)
//   motion.md        §3 Sheet (`duration-slow` slide, no content fade)
//   a11y.md          §3 Sheet (same focus trap as Dialog)
//
// Reuses Radix Dialog: same portal, backdrop, focus trap, Esc semantics.
// The variance is chrome: side prop drives slide direction and edge-fit.

import { cva, type VariantProps } from "class-variance-authority";
import { Dialog as SheetPrimitive } from "radix-ui";
import { X } from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";

// Fixed edge-anchored positioning per side + slide-in/out per side.
const sheetContentVariants = cva(
	[
		"fixed z-50 flex flex-col gap-4 bg-bg-elevated border-border-default text-text-primary shadow-lg",
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
			size: {
				// side-agnostic default fills the perpendicular axis; the
				// compoundVariants below map size to the correct axis.
				sm: "",
				md: "",
				lg: "",
			},
		},
		compoundVariants: [
			// left / right sheets: width sm/md/lg = 320/440/560, full height.
			{ side: "left", size: "sm", class: "h-full w-80" },
			{ side: "left", size: "md", class: "h-full w-[27.5rem]" },
			{ side: "left", size: "lg", class: "h-full w-[35rem]" },
			{ side: "right", size: "sm", class: "h-full w-80" },
			{ side: "right", size: "md", class: "h-full w-[27.5rem]" },
			{ side: "right", size: "lg", class: "h-full w-[35rem]" },
			// top / bottom sheets: height sm/md/lg = 240/320/440, full width.
			{ side: "top", size: "sm", class: "w-full h-60" },
			{ side: "top", size: "md", class: "w-full h-80" },
			{ side: "top", size: "lg", class: "w-full h-[27.5rem]" },
			{ side: "bottom", size: "sm", class: "w-full h-60" },
			{ side: "bottom", size: "md", class: "w-full h-80" },
			{ side: "bottom", size: "lg", class: "w-full h-[27.5rem]" },
		],
		defaultVariants: {
			side: "right",
			size: "md",
		},
	},
);

function Sheet({
	...props
}: React.ComponentProps<typeof SheetPrimitive.Root>) {
	return <SheetPrimitive.Root data-slot="sheet" {...props} />;
}

function SheetTrigger({
	...props
}: React.ComponentProps<typeof SheetPrimitive.Trigger>) {
	return <SheetPrimitive.Trigger data-slot="sheet-trigger" {...props} />;
}

function SheetClose({
	...props
}: React.ComponentProps<typeof SheetPrimitive.Close>) {
	return <SheetPrimitive.Close data-slot="sheet-close" {...props} />;
}

function SheetPortal({
	...props
}: React.ComponentProps<typeof SheetPrimitive.Portal>) {
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
	showClose?: boolean;
}

function SheetContent({
	className,
	side,
	size,
	children,
	showClose = true,
	...props
}: SheetContentProps) {
	return (
		<SheetPortal>
			<SheetOverlay />
			<SheetPrimitive.Content
				data-slot="sheet-content"
				className={cn(sheetContentVariants({ side, size }), className)}
				{...props}
			>
				{children}
				{showClose && (
					<SheetPrimitive.Close
						data-slot="sheet-close-icon"
						className={cn(
							"absolute right-4 top-4 rounded-sm text-text-secondary",
							"transition-colors duration-fast ease-out",
							"hover:text-text-primary",
							"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-elevated",
							"disabled:pointer-events-none",
						)}
					>
						<X className="size-4" />
						<span className="sr-only">Close</span>
					</SheetPrimitive.Close>
				)}
			</SheetPrimitive.Content>
		</SheetPortal>
	);
}

function SheetHeader({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="sheet-header"
			className={cn("flex flex-col gap-1.5 text-left", className)}
			{...props}
		/>
	);
}

function SheetFooter({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="sheet-footer"
			className={cn(
				"mt-auto flex flex-col gap-2 sm:flex-row sm:justify-end",
				className,
			)}
			{...props}
		/>
	);
}

function SheetTitle({
	className,
	...props
}: React.ComponentProps<typeof SheetPrimitive.Title>) {
	return (
		<SheetPrimitive.Title
			data-slot="sheet-title"
			className={cn(
				"text-2xl font-semibold leading-tight text-text-primary",
				className,
			)}
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
	SheetTrigger,
	SheetContent,
	SheetHeader,
	SheetFooter,
	SheetTitle,
	SheetDescription,
	SheetClose,
	SheetOverlay,
	SheetPortal,
	sheetContentVariants,
};
