// Bottom sheet: the touch-mode surface every kit overlay becomes.
// Design refs:
//   language/mobile.md  the mobile design language (overlays, sheets, sizing)
//   palette.md          backgrounds, borders
//   motion.md           `duration-slow`, ease out in, ease in out (index.css)
//
// Built on vaul, itself on Radix Dialog: same portal, focus trap, Esc and
// open / onOpenChange as Dialog and Sheet, plus drag down to dismiss. vaul is
// wrapped here and nowhere else, so swapping it is this one file.
//
// The sheet rides up with the on-screen keyboard on its own
// (../../lib/on-screen-keyboard.ts), not with vaul's `repositionInputs`: that
// one also sets the sheet's height from where its top sits as the keyboard
// opens, and on iOS, where the page pans as it opens, a short form stretched
// to most of the screen. Here the sheet is lifted by exactly what the
// keyboard covers and capped to the room left above it; its height stays its
// content's.
//
// One shape: anchored to the bottom, as tall as its content, capped at 90% of
// the viewport, the body scrolling inside past that. A grab handle on top, the
// home indicator's safe area under the last row.
//
// Popover, select, menus, pickers and dialogs render this in touch mode
// (../../lib/touch.ts): the same component API, a different presentation.
// See popover.tsx for the pattern.

import { cva, type VariantProps } from "class-variance-authority";
import { VisuallyHidden } from "radix-ui";
import type * as React from "react";
import { Drawer as Vaul } from "vaul";

import { useOnScreenKeyboard } from "../../lib/on-screen-keyboard";
import { usePortalContainer } from "../../lib/portal";
import { cn } from "../../lib/utils";

function BottomSheet({ ...props }: React.ComponentProps<typeof Vaul.Root>) {
	// The keyboard is the content's to follow (`BottomSheetContent`).
	return <Vaul.Root repositionInputs={false} {...props} />;
}

function BottomSheetTrigger({ ...props }: React.ComponentProps<typeof Vaul.Trigger>) {
	return <Vaul.Trigger data-slot="bottom-sheet-trigger" {...props} />;
}

function BottomSheetClose({ ...props }: React.ComponentProps<typeof Vaul.Close>) {
	return <Vaul.Close data-slot="bottom-sheet-close" {...props} />;
}

export interface BottomSheetContentProps
	extends Omit<React.ComponentProps<typeof Vaul.Content>, "title"> {
	/** A visible title over the body. */
	title?: React.ReactNode;
	/**
	 * The sheet's accessible name when it shows no title (a menu, a list of
	 * options). Ignored when `title` is set, or when the body has its own
	 * `BottomSheetTitle`.
	 */
	label?: string;
	/** Classes for the scrolling body, where the children go. */
	bodyClassName?: string;
	/** Portal into this element rather than the body (or a full screen surface). */
	container?: HTMLElement | null;
}

function BottomSheetContent({
	className,
	bodyClassName,
	title,
	label,
	container,
	children,
	style,
	...props
}: BottomSheetContentProps) {
	// Up with the keyboard: lifted by what it covers, at most 90% of what is
	// left above it, no safe area under it (the keyboard is there instead).
	const keyboard = useOnScreenKeyboard();
	const lifted: React.CSSProperties | undefined = keyboard.inset
		? {
				bottom: keyboard.inset,
				maxHeight: Math.round(keyboard.visible * 0.9),
				paddingBottom: 0,
			}
		: undefined;
	return (
		<Vaul.Portal container={usePortalContainer(container)}>
			<Vaul.Overlay data-slot="bottom-sheet-overlay" className="fixed inset-0 z-50 bg-bg-overlay" />
			<Vaul.Content
				aria-describedby={undefined}
				className={cn(
					"fixed inset-x-0 bottom-0 z-50 flex max-h-[90dvh] flex-col outline-hidden",
					"bg-bg-elevated text-text-primary border-t border-border-default rounded-t-xl shadow-modal",
					"pb-[env(safe-area-inset-bottom)]",
					className,
				)}
				{...props}
				style={lifted ? { ...style, ...lifted } : style}
				data-keyboard={keyboard.inset ? "" : undefined}
				// After the props: the motion CSS keys on this slot, so a caller cannot replace it.
				data-slot="bottom-sheet-content"
			>
				<div
					aria-hidden="true"
					data-slot="bottom-sheet-handle"
					className="mx-auto mt-2 mb-2 h-1 w-9 shrink-0 rounded-full bg-border-strong"
				/>
				{title != null ? (
					<BottomSheetHeader>
						<BottomSheetTitle>{title}</BottomSheetTitle>
					</BottomSheetHeader>
				) : label ? (
					<VisuallyHidden.Root asChild>
						<Vaul.Title>{label}</Vaul.Title>
					</VisuallyHidden.Root>
				) : null}
				<div
					data-slot="bottom-sheet-body"
					className={cn(
						"min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 pb-4",
						bodyClassName,
					)}
				>
					{children}
				</div>
			</Vaul.Content>
		</Vaul.Portal>
	);
}

function BottomSheetHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="bottom-sheet-header"
			className={cn("flex shrink-0 flex-col gap-1 px-4 pb-3", className)}
			{...props}
		/>
	);
}

// Actions under the body: full width, stacked, the primary one first.
function BottomSheetFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="bottom-sheet-footer"
			className={cn("flex flex-col gap-2 pt-3 [&>*]:w-full", className)}
			{...props}
		/>
	);
}

function BottomSheetTitle({ className, ...props }: React.ComponentProps<typeof Vaul.Title>) {
	return (
		<Vaul.Title
			data-slot="bottom-sheet-title"
			className={cn("text-lg font-semibold leading-tight text-text-primary", className)}
			{...props}
		/>
	);
}

function BottomSheetDescription({
	className,
	...props
}: React.ComponentProps<typeof Vaul.Description>) {
	return (
		<Vaul.Description
			data-slot="bottom-sheet-description"
			className={cn("text-sm text-text-secondary", className)}
			{...props}
		/>
	);
}

// One row of a sheet's list: a menu item, an option, an action. 44px, the
// sheet being a kit-owned surface sized for the thumb for real.
const bottomSheetItemVariants = cva(
	[
		"flex w-full min-h-tap items-center gap-3 px-1 text-left text-base",
		"border-b border-border-subtle last:border-b-0",
		"cursor-default outline-hidden",
		"active:bg-bg-press focus-visible:bg-bg-hover",
		"disabled:pointer-events-none disabled:opacity-50",
		"[&_svg]:size-4 [&_svg]:shrink-0 [&_svg]:text-text-muted",
	].join(" "),
	{
		variants: {
			variant: {
				default: "text-text-primary",
				danger: "text-status-danger [&_svg]:text-status-danger",
			},
			selected: {
				true: "font-medium",
				false: "",
			},
		},
		defaultVariants: { variant: "default", selected: false },
	},
);

export interface BottomSheetItemProps
	extends React.ButtonHTMLAttributes<HTMLButtonElement>,
		VariantProps<typeof bottomSheetItemVariants> {}

function BottomSheetItem({
	className,
	variant,
	selected,
	type = "button",
	...props
}: BottomSheetItemProps) {
	return (
		<button
			type={type}
			data-slot="bottom-sheet-item"
			data-selected={selected || undefined}
			className={cn(bottomSheetItemVariants({ variant, selected }), className)}
			{...props}
		/>
	);
}

export {
	BottomSheet,
	BottomSheetClose,
	BottomSheetContent,
	BottomSheetDescription,
	BottomSheetFooter,
	BottomSheetHeader,
	BottomSheetItem,
	BottomSheetTitle,
	BottomSheetTrigger,
	bottomSheetItemVariants,
};
