// Dialog primitive: modal surface with backdrop scrim, focus-trap, Esc-to-close.
// Design refs:
//   primitives.md    §Dialog (parts, sizes, states)
//   palette.md       backgrounds (`bg-bg-elevated`, `bg-bg-overlay`)
//   space-radius.md  §Density Dialog (pad 24, radius `lg`)
//   motion.md        §3 Dialog (overlay + content: `duration-slow` fade+scale)
//   a11y.md          §3 Dialog (focus trap, Esc, focus restore)
//
// In touch mode (../../lib/touch.ts) a dialog is a bottom sheet
// (./bottom-sheet.tsx), the popover pattern (./popover.tsx): the root,
// trigger, close, title and description map one to one, the content fills
// the sheet and drops its width, the corner close icon is gone (the sheet
// drags down, and a tap outside or back closes it), and the footer stacks
// its actions full width, the main one first. A dialog that already covers
// the window, like the image viewer's full view, opts out with
// `sheet={false}` and stays a dialog.

import { cva } from "class-variance-authority";
import { X } from "lucide-react";
import { Dialog as DialogPrimitive } from "radix-ui";
import * as React from "react";

import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import {
	BottomSheet,
	BottomSheetClose,
	BottomSheetContent,
	BottomSheetDescription,
	BottomSheetTitle,
	BottomSheetTrigger,
} from "./bottom-sheet";
import { IconButton } from "./icon-button";

// `width` caps the content (512px unless set: a number is px, text any CSS
// length) and stays fluid under it, so the dialog fits a narrow window; the
// content decides height and scroll. The wire's word, as on Modal.
const dialogContentVariants = cva(
	[
		// One column that may shrink below its content, so a long one-line
		// title cuts instead of widening the dialog past its max width.
		"fixed left-1/2 top-1/2 z-50 grid w-full max-w-lg grid-cols-[minmax(0,1fr)] -translate-x-1/2 -translate-y-1/2 gap-4",
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

// Whether the dialog above is a bottom sheet. Set by the root, so its parts
// follow the root's choice (a `sheet={false}` dialog stays a dialog in touch
// mode); outside a root, the touch mode decides.
const SheetContext = React.createContext<boolean | undefined>(undefined);

function useSheet(): boolean {
	const touch = useTouch();
	return React.useContext(SheetContext) ?? touch;
}

export interface DialogProps extends React.ComponentProps<typeof DialogPrimitive.Root> {
	/**
	 * In touch mode, show as a bottom sheet (the default). False keeps the
	 * dialog as it is, for one that already covers the window.
	 */
	sheet?: boolean;
	/**
	 * False: the user cannot close the sheet (drag, tap outside, Esc), only
	 * `open` can. On desktop it does nothing, a controlled dialog refuses a
	 * close in `onOpenChange`; a sheet would still drag away, so a dialog
	 * that refuses passes this too.
	 */
	dismissible?: boolean;
}

function Dialog({ sheet = true, dismissible = true, ...props }: DialogProps) {
	const touch = useTouch();
	const asSheet = touch && sheet;
	if (asSheet) {
		const { open, defaultOpen, onOpenChange, children } = props;
		return (
			<SheetContext.Provider value={true}>
				<BottomSheet
					open={open}
					defaultOpen={defaultOpen}
					onOpenChange={onOpenChange}
					dismissible={dismissible}
				>
					{children}
				</BottomSheet>
			</SheetContext.Provider>
		);
	}
	return (
		<SheetContext.Provider value={false}>
			<DialogPrimitive.Root data-slot="dialog" {...props} />
		</SheetContext.Provider>
	);
}

function DialogTrigger({ ...props }: React.ComponentProps<typeof DialogPrimitive.Trigger>) {
	const sheet = useSheet();
	if (sheet) return <BottomSheetTrigger data-slot="dialog-trigger" {...props} />;
	return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />;
}

function DialogClose({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Close>) {
	const sheet = useSheet();
	if (sheet) {
		return (
			<BottomSheetClose
				data-slot="dialog-close"
				className={cn("cursor-default", className)}
				{...props}
			/>
		);
	}
	return (
		<DialogPrimitive.Close
			data-slot="dialog-close"
			className={cn("cursor-default", className)}
			{...props}
		/>
	);
}

// Portal and overlay are the desktop dialog's own parts. The sheet brings
// its own, so in touch mode the portal passes its children through and the
// overlay draws nothing.
function DialogPortal({ ...props }: React.ComponentProps<typeof DialogPrimitive.Portal>) {
	const sheet = useSheet();
	if (sheet) return <>{props.children}</>;
	return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />;
}

function DialogOverlay({
	className,
	...props
}: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
	const sheet = useSheet();
	if (sheet) return null;
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
	const sheet = useSheet();
	const cap = lengthCss(width);
	if (sheet) {
		// The sheet is the window's width, so the width props go. The caller's
		// classes style the body, laid out the way the dialog lays out its
		// children: one column, 16 apart. The rest of the style (a height, for
		// a big form that wants the sheet tall) sits on the sheet.
		const { width: _width, minWidth: _minWidth, maxWidth: _maxWidth, ...rest } = style ?? {};
		return (
			<BottomSheetContent
				style={rest}
				bodyClassName={cn("grid grid-cols-[minmax(0,1fr)] content-start gap-4", className)}
				{...props}
			>
				{children}
			</BottomSheetContent>
		);
	}
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
			className={cn("flex min-w-0 flex-col gap-1.5 text-left", className)}
			{...props}
		/>
	);
}

// Actions in source order, the main one last. On a sheet they stack full
// width with the main one first, the reverse of the row, so the same
// children read right on both.
function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	const sheet = useSheet();
	return (
		<div
			data-slot="dialog-footer"
			className={cn(
				sheet
					? "flex flex-col-reverse gap-2 [&>*]:w-full"
					: "flex flex-col-reverse gap-2 sm:flex-row sm:justify-end",
				className,
			)}
			{...props}
		/>
	);
}

// On a sheet the title keeps the dialog's look, it only names the sheet.
function DialogTitle({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Title>) {
	const sheet = useSheet();
	if (sheet) {
		return (
			<BottomSheetTitle
				data-slot="dialog-title"
				className={cn("text-2xl font-semibold leading-tight text-text-primary", className)}
				{...props}
			/>
		);
	}
	return (
		<DialogPrimitive.Title
			data-slot="dialog-title"
			className={cn("text-2xl font-semibold leading-tight text-text-primary", className)}
			{...props}
		/>
	);
}

// The dialog's title as a plain box the caller fills: a header line made of
// other parts (an icon, a name, a badge) in place of a string. It is still
// Radix's Title, so the dialog is named by its text, but it brings no type
// of its own, and it takes the width while letting its content shrink.
function DialogTitleBox({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	// The same in touch mode: the sheet's root is a Radix Dialog root too
	// (./bottom-sheet.tsx), so Radix's title names it, and a box brings no
	// type of its own the way the sheet's title would.
	return (
		<DialogPrimitive.Title asChild>
			<div data-slot="dialog-title-box" className={cn("min-w-0", className)} {...props} />
		</DialogPrimitive.Title>
	);
}

function DialogDescription({
	className,
	...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
	const sheet = useSheet();
	if (sheet) {
		return (
			<BottomSheetDescription
				data-slot="dialog-description"
				className={cn("text-sm text-text-secondary", className)}
				{...props}
			/>
		);
	}
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
	DialogTitleBox,
	DialogTrigger,
	dialogContentVariants,
};
