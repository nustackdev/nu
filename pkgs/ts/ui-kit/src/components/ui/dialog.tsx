// Dialog primitive: modal surface with backdrop scrim, focus-trap, Esc-to-close.
// Design refs:
//   primitives.md    §Dialog (parts, sizes, states)
//   palette.md       backgrounds (`bg-bg-elevated`, `bg-bg-overlay`)
//   space-radius.md  §Density Dialog (pad 24, radius `lg`)
//   motion.md        §3 Dialog (overlay + content: `duration-slow` fade+scale)
//   a11y.md          §3 Dialog (focus trap, Esc, focus restore)

import { cva } from "class-variance-authority";
import { X } from "lucide-react";
import { Dialog as DialogPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";
import { IconButton } from "./icon-button";

// `width` caps the content (512px unless set: a number is px, text any CSS
// length) and stays fluid under it, so the dialog fits a narrow window; the
// content decides height and scroll. The wire's word, as on Modal.
const dialogContentVariants = cva(
	[
		"fixed left-1/2 top-1/2 z-50 grid w-full max-w-lg -translate-x-1/2 -translate-y-1/2 gap-4",
		"bg-bg-elevated text-text-primary border border-border-default rounded-lg shadow-modal",
		"p-6",
		// Motion tokens per motion.md §3 Dialog.
		"data-[state=open]:animate-in data-[state=closed]:animate-out",
		"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
		"data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95",
		"data-[state=open]:duration-slow data-[state=closed]:duration-slow",
		"data-[state=open]:ease-out data-[state=closed]:ease-in",
	].join(" "),
);

/** A length as CSS: a number is px, text passes as written. */
export function lengthCss(value: number | string | undefined): string | undefined {
	return typeof value === "number" ? `${value}px` : value;
}

function Dialog({ ...props }: React.ComponentProps<typeof DialogPrimitive.Root>) {
	return <DialogPrimitive.Root data-slot="dialog" {...props} />;
}

function DialogTrigger({ ...props }: React.ComponentProps<typeof DialogPrimitive.Trigger>) {
	return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />;
}

function DialogClose({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Close>) {
	return (
		<DialogPrimitive.Close
			data-slot="dialog-close"
			className={cn("cursor-default", className)}
			{...props}
		/>
	);
}

function DialogPortal({ ...props }: React.ComponentProps<typeof DialogPrimitive.Portal>) {
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

export interface DialogContentProps extends React.ComponentProps<typeof DialogPrimitive.Content> {
	/** The dialog's width, a cap it stays fluid under: px, or a CSS length. 512px unless set. */
	width?: number | string;
	// Show the built-in top-right close icon. Off when the caller renders
	// their own DialogClose inside the content.
	showClose?: boolean;
}

function DialogContent({
	className,
	width,
	style,
	children,
	showClose = true,
	...props
}: DialogContentProps) {
	const cap = lengthCss(width);
	return (
		<DialogPortal>
			<DialogOverlay />
			<DialogPrimitive.Content
				data-slot="dialog-content"
				className={cn(dialogContentVariants(), className)}
				style={cap === undefined ? style : { maxWidth: cap, ...style }}
				{...props}
			>
				{children}
				{showClose && (
					// A kit IconButton, like every other icon-only control: a box,
					// a hover wash, the inset ring.
					<DialogPrimitive.Close asChild>
						<IconButton
							data-slot="dialog-close-icon"
							variant="ghost"
							size="sm"
							ring="inset"
							aria-label="Close"
							className="absolute right-4 top-4"
						>
							<X />
						</IconButton>
					</DialogPrimitive.Close>
				)}
			</DialogPrimitive.Content>
		</DialogPortal>
	);
}

function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="dialog-header"
			className={cn("flex flex-col gap-1.5 text-left", className)}
			{...props}
		/>
	);
}

function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="dialog-footer"
			className={cn("flex flex-col-reverse gap-2 sm:flex-row sm:justify-end", className)}
			{...props}
		/>
	);
}

function DialogTitle({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Title>) {
	return (
		<DialogPrimitive.Title
			data-slot="dialog-title"
			className={cn("text-2xl font-semibold leading-tight text-text-primary", className)}
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
	DialogClose,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogOverlay,
	DialogPortal,
	DialogTitle,
	DialogTrigger,
	dialogContentVariants,
};
