// Dialog primitive: modal surface with backdrop scrim, focus-trap, Esc-to-close.
// Design refs:
//   primitives.md    §Dialog (parts, sizes, states)
//   palette.md       §2.1 backgrounds (`bg-bg-elevated`, `bg-bg-overlay`)
//   space-radius.md  §Density Dialog (pad 24, radius `lg`)
//   motion.md        §3 Dialog (overlay + content: `duration-slow` fade+scale)
//   a11y.md          §3 Dialog (focus trap, Esc, focus restore)

import { cva, type VariantProps } from "class-variance-authority";
import { Dialog as DialogPrimitive } from "radix-ui";
import { X } from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";

// Sizes cap content max-width; consumer content decides height / scroll.
// Values sit one step above shadcn defaults so IDE dashboards read roomier
// on wide monitors without ballooning on narrow ones.
const dialogContentVariants = cva(
	[
		"fixed left-1/2 top-1/2 z-50 grid w-full -translate-x-1/2 -translate-y-1/2 gap-4",
		"bg-bg-elevated text-text-primary border border-border-default rounded-lg shadow-lg",
		"p-6",
		// Motion tokens per motion.md §3 Dialog.
		"data-[state=open]:animate-in data-[state=closed]:animate-out",
		"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
		"data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95",
		"data-[state=open]:duration-slow data-[state=closed]:duration-slow",
		"data-[state=open]:ease-out data-[state=closed]:ease-in",
	].join(" "),
	{
		variants: {
			size: {
				sm: "max-w-sm",
				md: "max-w-lg",
				lg: "max-w-2xl",
				xl: "max-w-4xl",
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

function Dialog({
	...props
}: React.ComponentProps<typeof DialogPrimitive.Root>) {
	return <DialogPrimitive.Root data-slot="dialog" {...props} />;
}

function DialogTrigger({
	...props
}: React.ComponentProps<typeof DialogPrimitive.Trigger>) {
	return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />;
}

function DialogClose({
	...props
}: React.ComponentProps<typeof DialogPrimitive.Close>) {
	return <DialogPrimitive.Close data-slot="dialog-close" {...props} />;
}

function DialogPortal({
	...props
}: React.ComponentProps<typeof DialogPrimitive.Portal>) {
	return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />;
}

function DialogOverlay({
	className,
	...props
}: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
	return (
		<DialogPrimitive.Overlay
			data-slot="dialog-overlay"
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

export interface DialogContentProps
	extends React.ComponentProps<typeof DialogPrimitive.Content>,
		VariantProps<typeof dialogContentVariants> {
	// Show the built-in top-right close icon. Off when the caller renders
	// their own DialogClose inside the content.
	showClose?: boolean;
}

function DialogContent({
	className,
	size,
	children,
	showClose = true,
	...props
}: DialogContentProps) {
	return (
		<DialogPortal>
			<DialogOverlay />
			<DialogPrimitive.Content
				data-slot="dialog-content"
				className={cn(dialogContentVariants({ size }), className)}
				{...props}
			>
				{children}
				{showClose && (
					<DialogPrimitive.Close
						data-slot="dialog-close-icon"
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
					</DialogPrimitive.Close>
				)}
			</DialogPrimitive.Content>
		</DialogPortal>
	);
}

function DialogHeader({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="dialog-header"
			className={cn("flex flex-col gap-1.5 text-left", className)}
			{...props}
		/>
	);
}

function DialogFooter({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="dialog-footer"
			className={cn(
				"flex flex-col-reverse gap-2 sm:flex-row sm:justify-end",
				className,
			)}
			{...props}
		/>
	);
}

function DialogTitle({
	className,
	...props
}: React.ComponentProps<typeof DialogPrimitive.Title>) {
	return (
		<DialogPrimitive.Title
			data-slot="dialog-title"
			className={cn(
				"text-2xl font-semibold leading-tight text-text-primary",
				className,
			)}
			{...props}
		/>
	);
}

function DialogDescription({
	className,
	...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
	return (
		<DialogPrimitive.Description
			data-slot="dialog-description"
			className={cn("text-sm text-text-secondary", className)}
			{...props}
		/>
	);
}

export {
	Dialog,
	DialogTrigger,
	DialogContent,
	DialogHeader,
	DialogFooter,
	DialogTitle,
	DialogDescription,
	DialogClose,
	DialogOverlay,
	DialogPortal,
	dialogContentVariants,
};
