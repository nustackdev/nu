// Toast primitive: a short, non-modal notice that comes and goes on its own.
// Design refs:
//   primitives.md    §Alert (tone triple: wash, line, icon)
//   palette.md       backgrounds (`bg-bg-elevated`), status tones
//   space-radius.md  §Density (pad 12, radius `md`)
//   motion.md        §Property picks (Toast: fade + slight y-shift)
//   a11y.md          §7 (role per tone: danger is assertive, the rest polite)
//
// Two parts. `Toaster` is mounted once near the app root and draws every
// toast in a corner stack. `toast()` shows one from anywhere, an event
// handler or a socket write, with no hook and no context: it returns the
// toast's id, and `dismissToast(id)` takes it down early. Built on Radix
// Toast, which brings the swipe to dismiss, the pause on hover and focus, and
// the F8 hotkey into the stack.

import { cva } from "class-variance-authority";
import { AlertCircle, AlertTriangle, Bell, CheckCircle2, Info, type LucideIcon, X } from "lucide-react";
import { Toast as ToastPrimitive } from "radix-ui";
import * as React from "react";

import { cn } from "../../lib/utils";
import { IconButton } from "./icon-button";

export type ToastTone = "neutral" | "info" | "ok" | "warn" | "danger";

export interface ToastOptions {
	/** The one line that says what happened. */
	title: string;
	/** What to know beyond it, two lines at most in most uses. */
	description?: string;
	tone?: ToastTone;
	/** How long it stays, in ms. Danger stays longer by default. */
	duration?: number;
}

export interface ToastEntry extends Required<Omit<ToastOptions, "description">> {
	id: number;
	description: string;
	open: boolean;
}

/** How long a toast stays when nothing says otherwise, in ms. */
export const TOAST_DURATION = 5000;
/** How long a danger toast stays: an error is read, not glanced at. */
export const TOAST_DANGER_DURATION = 8000;
/** Toasts kept on screen at once; the oldest goes first. */
export const TOAST_LIMIT = 4;

// -- The store: module level, so toast() works from anywhere ------------------

let entries: ToastEntry[] = [];
let nextId = 1;
const subscribers = new Set<() => void>();

function emit(): void {
	for (const cb of subscribers) cb();
}

function subscribe(cb: () => void): () => void {
	subscribers.add(cb);
	return () => subscribers.delete(cb);
}

function snapshot(): ToastEntry[] {
	return entries;
}

/** Show a toast. Returns its id, for `dismissToast`. */
export function toast(options: ToastOptions): number {
	const tone = options.tone ?? "neutral";
	const entry: ToastEntry = {
		id: nextId++,
		title: options.title,
		description: options.description ?? "",
		tone,
		duration: options.duration ?? (tone === "danger" ? TOAST_DANGER_DURATION : TOAST_DURATION),
		open: true,
	};
	// Closed ones are done animating by the next toast: drop them here.
	entries = [...entries.filter((e) => e.open), entry].slice(-TOAST_LIMIT);
	emit();
	return entry.id;
}

/** Take a toast down before its time. A no-op for one already gone. */
export function dismissToast(id: number): void {
	if (!entries.some((e) => e.id === id && e.open)) return;
	entries = entries.map((e) => (e.id === id ? { ...e, open: false } : e));
	emit();
}

/** The toasts on screen now. For tests and for a host that draws its own stack. */
export function useToasts(): ToastEntry[] {
	return React.useSyncExternalStore(subscribe, snapshot, snapshot);
}

// -- The parts ----------------------------------------------------------------

const toastVariants = cva(
	[
		"pointer-events-auto relative flex w-full items-start gap-3 rounded-md border p-3 pr-9",
		"bg-bg-elevated text-text-primary shadow-floating font-display text-sm",
		// Motion per motion.md: fade + slight y-shift.
		"data-[state=open]:animate-in data-[state=closed]:animate-out",
		"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
		"data-[state=open]:slide-in-from-bottom-1 data-[state=closed]:slide-out-to-bottom-1",
		"data-[state=open]:duration-base data-[state=closed]:duration-fast",
		"data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)]",
		"data-[swipe=cancel]:translate-x-0 data-[swipe=end]:animate-out data-[swipe=end]:fade-out-0",
	].join(" "),
	{
		variants: {
			tone: {
				neutral: "border-border-default",
				info: "border-status-info-line",
				ok: "border-status-ok-line",
				warn: "border-status-warn-line",
				danger: "border-status-danger-line bg-status-danger-wash",
			},
		},
		defaultVariants: { tone: "neutral" },
	},
);

const ICONS: Record<ToastTone, LucideIcon> = {
	neutral: Bell,
	info: Info,
	ok: CheckCircle2,
	warn: AlertCircle,
	danger: AlertTriangle,
};

const ICON_TONE: Record<ToastTone, string> = {
	neutral: "text-text-secondary",
	info: "text-status-info",
	ok: "text-status-ok",
	warn: "text-status-warn",
	danger: "text-status-danger",
};

export interface ToastProps extends React.ComponentProps<typeof ToastPrimitive.Root> {
	tone?: ToastTone;
	title: string;
	description?: string;
}

/** One toast, as `Toaster` draws it. Usable alone inside a `ToastPrimitive.Provider`. */
export function Toast({ tone = "neutral", title, description, className, ...props }: ToastProps) {
	const Icon = ICONS[tone];
	return (
		<ToastPrimitive.Root
			data-slot="toast"
			data-tone={tone}
			type={tone === "danger" ? "foreground" : "background"}
			className={cn(toastVariants({ tone }), className)}
			{...props}
		>
			<Icon aria-hidden="true" className={cn("mt-0.5 size-4 shrink-0", ICON_TONE[tone])} />
			<div className="min-w-0 flex-1">
				<ToastPrimitive.Title className="font-semibold leading-tight break-words">
					{title}
				</ToastPrimitive.Title>
				{description ? (
					<ToastPrimitive.Description className="mt-0.5 text-text-secondary leading-normal break-words">
						{description}
					</ToastPrimitive.Description>
				) : null}
			</div>
			<ToastPrimitive.Close asChild>
				<IconButton
					aria-label="Dismiss"
					variant="ghost"
					size="xs"
					className="absolute right-2 top-2"
				>
					<X />
				</IconButton>
			</ToastPrimitive.Close>
		</ToastPrimitive.Root>
	);
}

export interface ToasterProps {
	className?: string;
	/** What screen readers call the stack. */
	label?: string;
}

/** The stack every `toast()` lands in. Mount it once, near the app root. */
export function Toaster({ className, label = "Notifications" }: ToasterProps) {
	const shown = useToasts();
	return (
		<ToastPrimitive.Provider swipeDirection="right" label={label}>
			{shown.map((t) => (
				<Toast
					key={t.id}
					tone={t.tone}
					title={t.title}
					description={t.description}
					duration={t.duration}
					open={t.open}
					onOpenChange={(open) => {
						if (!open) dismissToast(t.id);
					}}
				/>
			))}
			<ToastPrimitive.Viewport
				data-slot="toast-viewport"
				className={cn(
					"fixed bottom-0 right-0 z-50 flex max-h-screen w-full max-w-sm flex-col gap-2 p-4 outline-none",
					className,
				)}
			/>
		</ToastPrimitive.Provider>
	);
}
