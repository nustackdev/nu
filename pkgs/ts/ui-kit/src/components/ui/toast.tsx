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
// toast's id, and `dismissToast(id)` takes it down early. A toast may carry
// one action, a button beside its text (an Undo): clicking it runs the
// action and closes the toast. Built on Radix
// Toast, which brings the swipe to dismiss, the pause on hover and focus, and
// the F8 hotkey into the stack.
//
// In touch mode (../../lib/touch.ts) the stack moves to the top edge, clear of
// the thumb, the on-screen keyboard and the buttons at the bottom of the
// screen, under the notch's safe area. The newest sits on top, a toast drops
// in from above and is swiped up to go. Same toasts, same API.

import { cva } from "class-variance-authority";
import {
	AlertCircle,
	AlertTriangle,
	Bell,
	CheckCircle2,
	Info,
	type LucideIcon,
	X,
} from "lucide-react";
import { Toast as ToastPrimitive } from "radix-ui";
import * as React from "react";

import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import { Button } from "./button";
import { IconButton } from "./icon-button";

export type ToastTone = "neutral" | "info" | "ok" | "warn" | "danger";

/** The one button a toast may carry beside its text, eg an Undo. */
export interface ToastAction {
	/** What the button says, short: one word in most uses. */
	label: string;
	/** Runs on click; the toast closes with it. */
	onClick: () => void;
}

export interface ToastOptions {
	/** The one line that says what happened. */
	title: string;
	/** What to know beyond it, two lines at most in most uses. */
	description?: string;
	tone?: ToastTone;
	/** How long it stays, in ms. Danger stays longer by default. */
	duration?: number;
	/** A button beside the text. */
	action?: ToastAction;
}

export interface ToastEntry extends Required<Omit<ToastOptions, "description" | "action">> {
	id: number;
	description: string;
	action: ToastAction | null;
	open: boolean;
}

/** How long a toast stays when nothing says otherwise, in ms. */
export const TOAST_DURATION = 5000;
/** How long a danger toast stays: an error is read, not glanced at. */
export const TOAST_DANGER_DURATION = 8000;
/** Toasts kept on screen at once; the oldest goes first. */
export const TOAST_LIMIT = 4;
/** How long a closed toast stays drawn, in ms: past its fade out (`duration-fast`, 120 ms). */
export const TOAST_EXIT = 200;

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

// A closed toast stays in the stack, drawn closed, until its fade out is over,
// then leaves it: closing never cuts the animation short.
function close(ids: Set<number>): void {
	entries = entries.map((e) => (ids.has(e.id) ? { ...e, open: false } : e));
	setTimeout(() => {
		entries = entries.filter((e) => !ids.has(e.id));
		emit();
	}, TOAST_EXIT);
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
		action: options.action ?? null,
		open: true,
	};
	entries = [...entries, entry];
	// Past the limit the oldest open ones close, and fade out like any other.
	const open = entries.filter((e) => e.open);
	if (open.length > TOAST_LIMIT) close(new Set(open.slice(0, -TOAST_LIMIT).map((e) => e.id)));
	emit();
	return entry.id;
}

/** Take a toast down before its time. A no-op for one already closed or gone. */
export function dismissToast(id: number): void {
	if (!entries.some((e) => e.id === id && e.open)) return;
	close(new Set([id]));
	emit();
}

/** The toasts on screen now. For tests and for a host that draws its own stack. */
export function useToasts(): ToastEntry[] {
	return React.useSyncExternalStore(subscribe, snapshot, snapshot);
}

// -- The parts ----------------------------------------------------------------

const toastVariants = cva(
	[
		"pointer-events-auto relative flex w-full items-start gap-3 overflow-hidden rounded-md border p-3",
		"bg-bg-elevated text-text-primary shadow-floating font-display text-sm",
		// Motion per motion.md: fade + slight y-shift.
		"data-[state=open]:animate-in data-[state=closed]:animate-out",
		"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
		"data-[state=open]:duration-base data-[state=closed]:duration-fast",
		"data-[swipe=end]:animate-out data-[swipe=end]:fade-out-0",
	].join(" "),
	{
		variants: {
			// The edge the stack sits on: the shift comes from it, the swipe goes
			// back to it on touch, off to the side on desktop.
			edge: {
				bottom: [
					"data-[state=open]:slide-in-from-bottom-1 data-[state=closed]:slide-out-to-bottom-1",
					"data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=cancel]:translate-x-0",
				].join(" "),
				top: [
					"data-[state=open]:slide-in-from-top-1 data-[state=closed]:slide-out-to-top-1",
					"data-[swipe=move]:translate-y-[var(--radix-toast-swipe-move-y)] data-[swipe=cancel]:translate-y-0",
				].join(" "),
			},
			tone: {
				neutral: "border-border-default",
				info: "border-status-info-line",
				ok: "border-status-ok-line",
				warn: "border-status-warn-line",
				danger: "border-status-danger-line bg-status-danger-wash",
			},
		},
		defaultVariants: { tone: "neutral", edge: "bottom" },
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

const TIMER_TONE: Record<ToastTone, string> = {
	neutral: "bg-text-muted",
	info: "bg-status-info",
	ok: "bg-status-ok",
	warn: "bg-status-warn",
	danger: "bg-status-danger",
};

/**
 * The time left, as a line along the bottom edge that shrinks to nothing as
 * the toast closes. It holds while the toast's own timer does (hover, focus,
 * the window in the background): `paused` follows Radix's pause and resume.
 */
function ToastTimer({
	duration,
	paused,
	tone,
}: {
	duration: number;
	paused: boolean;
	tone: ToastTone;
}) {
	const ref = React.useRef<HTMLDivElement | null>(null);
	const run = React.useRef<Animation | null>(null);

	React.useEffect(() => {
		const el = ref.current;
		if (!el || typeof el.animate !== "function" || !Number.isFinite(duration)) return;
		const anim = el.animate([{ transform: "scaleX(1)" }, { transform: "scaleX(0)" }], {
			duration,
			easing: "linear",
			fill: "forwards",
		});
		run.current = anim;
		return () => anim.cancel();
	}, [duration]);

	React.useEffect(() => {
		if (paused) run.current?.pause();
		else run.current?.play();
	}, [paused]);

	return (
		<div
			ref={ref}
			aria-hidden="true"
			data-slot="toast-timer"
			className={cn(
				"pointer-events-none absolute inset-x-0 bottom-0 h-0.5 origin-left",
				TIMER_TONE[tone],
			)}
		/>
	);
}

export interface ToastProps extends React.ComponentProps<typeof ToastPrimitive.Root> {
	tone?: ToastTone;
	title: string;
	description?: string;
	action?: ToastAction | null;
}

/** One toast, as `Toaster` draws it. Usable alone inside a `ToastPrimitive.Provider`. */
export function Toast({
	tone = "neutral",
	title,
	description,
	action,
	duration = TOAST_DURATION,
	onPause,
	onResume,
	className,
	...props
}: ToastProps) {
	const touch = useTouch();
	const Icon = ICONS[tone];
	const [paused, setPaused] = React.useState(false);
	return (
		<ToastPrimitive.Root
			data-slot="toast"
			data-tone={tone}
			type={tone === "danger" ? "foreground" : "background"}
			className={cn(toastVariants({ tone, edge: touch ? "top" : "bottom" }), className)}
			duration={duration}
			onPause={() => {
				setPaused(true);
				onPause?.();
			}}
			onResume={() => {
				setPaused(false);
				onResume?.();
			}}
			{...props}
		>
			<ToastTimer duration={duration} paused={paused} tone={tone} />
			<Icon aria-hidden="true" className={cn("mt-0.5 size-4 shrink-0", ICON_TONE[tone])} />
			<div className="min-w-0 flex-1">
				<ToastPrimitive.Title className="font-semibold leading-5 break-words">
					{title}
				</ToastPrimitive.Title>
				{description ? (
					<ToastPrimitive.Description className="mt-0.5 text-text-secondary leading-normal break-words">
						{description}
					</ToastPrimitive.Description>
				) : null}
			</div>
			{/* On the title's line: the action and the close, each one line tall. */}
			<div className="flex shrink-0 items-center gap-1">
				{action ? (
					<ToastPrimitive.Action asChild altText={action.label}>
						<Button
							variant="ghost"
							size="xs"
							className="font-semibold text-accent-text hover:text-accent-text"
							onClick={action.onClick}
						>
							{action.label}
						</Button>
					</ToastPrimitive.Action>
				) : null}
				<ToastPrimitive.Close asChild>
					<IconButton aria-label="Dismiss" variant="ghost" size="xs">
						<X />
					</IconButton>
				</ToastPrimitive.Close>
			</div>
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
	const touch = useTouch();
	const shown = useToasts();
	return (
		<ToastPrimitive.Provider swipeDirection={touch ? "up" : "right"} label={label}>
			{shown.map((t) => (
				<Toast
					key={t.id}
					tone={t.tone}
					title={t.title}
					description={t.description}
					action={t.action}
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
					touch
						? // Top and centred, the newest first, under the notch. The safe
							// area only ever adds to the usual edge air.
							[
								"fixed inset-x-0 top-0 z-50 mx-auto flex max-h-dvh w-full max-w-sm flex-col-reverse gap-2 p-4 outline-none",
								"pt-[max(1rem,env(safe-area-inset-top))]",
								"pl-[max(1rem,env(safe-area-inset-left))] pr-[max(1rem,env(safe-area-inset-right))]",
							]
						: "fixed bottom-0 right-0 z-50 flex max-h-screen w-full max-w-sm flex-col gap-2 p-4 outline-none",
					className,
				)}
			/>
		</ToastPrimitive.Provider>
	);
}
