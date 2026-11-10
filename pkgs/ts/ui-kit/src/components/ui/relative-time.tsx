// RelativeTime primitive. A stamp drawn as time from now, kept live in the
// browser.
//
// The server sends an absolute stamp (epoch ms) once; the string moves with
// the clock here, so a host never redraws for time passing. Two modes:
//   ago        "just now", "42s ago", "4m ago", "3h ago", "3d ago", "2mo ago"
//   duration   time since the stamp, two units: "12s", "3m 12s", "2h 4m",
//              "3d 4h", for uptime and running time
//
// Every instance shares one clock: a single timer set for the soonest moment
// any mounted stamp changes its text. A stamp under a minute old wakes every
// second, under an hour every minute, and so on, each on the exact boundary
// where its text turns over. The hover title is the absolute time.
//
// A stamp a little in the future (clock skew) reads as now. A missing or
// non-finite stamp draws a muted "-".

import type * as React from "react";
import { useEffect, useState } from "react";

import { cn } from "../../lib/utils";

export type RelativeTimeMode = "ago" | "duration";
export const RELATIVE_TIME_MODES: readonly RelativeTimeMode[] = ["ago", "duration"];

const S = 1_000;
const M = 60 * S;
const H = 60 * M;
const D = 24 * H;
const MO = 30 * D;
const Y = 365 * D;

/** Under this an "ago" stamp reads "just now". */
const JUST_NOW = 5 * S;

/** The text for `elapsed` ms since the stamp. */
export function formatRelativeTime(elapsed: number, mode: RelativeTimeMode = "ago"): string {
	const e = Math.max(0, elapsed);
	if (mode === "duration") {
		if (e < M) return `${Math.floor(e / S)}s`;
		if (e < H) return `${Math.floor(e / M)}m ${Math.floor((e % M) / S)}s`;
		if (e < D) return `${Math.floor(e / H)}h ${Math.floor((e % H) / M)}m`;
		return `${Math.floor(e / D)}d ${Math.floor((e % D) / H)}h`;
	}
	if (e < JUST_NOW) return "just now";
	if (e < M) return `${Math.floor(e / S)}s ago`;
	if (e < H) return `${Math.floor(e / M)}m ago`;
	if (e < D) return `${Math.floor(e / H)}h ago`;
	if (e < MO) return `${Math.floor(e / D)}d ago`;
	if (e < Y) return `${Math.floor(e / MO)}mo ago`;
	return `${Math.floor(e / Y)}y ago`;
}

/** The elapsed ms at which the text for `elapsed` next changes. */
export function nextChange(elapsed: number, mode: RelativeTimeMode = "ago"): number {
	const e = Math.max(0, elapsed);
	let unit: number;
	if (mode === "duration") unit = e < H ? S : e < D ? M : H;
	else if (e < JUST_NOW) return JUST_NOW;
	else unit = e < M ? S : e < H ? M : e < D ? H : e < MO ? D : e < Y ? MO : Y;
	return (Math.floor(e / unit) + 1) * unit;
}

const absolute = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "medium" });

/** The hover title: the stamp as a local date and time. */
export function formatAbsolute(ts: number): string {
	return absolute.format(new Date(ts));
}

// --- the shared clock ---------------------------------------------------------
//
// One timer for every mounted RelativeTime. Each asks to be woken once at its
// own due time; the timer is set for the soonest. A waiter is dropped before
// it fires, so a fired one never holds the timer at zero while React commits.

type Waiter = { due: number; fire: (now: number) => void };

const waiters = new Set<Waiter>();
let timer: ReturnType<typeof setTimeout> | undefined;
let timerAt = Number.POSITIVE_INFINITY;
// setTimeout overflows past a 32-bit delay and fires at once.
const MAX_DELAY = 2 ** 31 - 1;

function schedule() {
	let soonest = Number.POSITIVE_INFINITY;
	for (const w of waiters) soonest = Math.min(soonest, w.due);
	if (soonest === timerAt) return;
	if (timer !== undefined) clearTimeout(timer);
	timer = undefined;
	timerAt = soonest;
	if (soonest === Number.POSITIVE_INFINITY) return;
	timer = setTimeout(flush, Math.min(MAX_DELAY, Math.max(0, soonest - Date.now())));
}

function flush() {
	timer = undefined;
	timerAt = Number.POSITIVE_INFINITY;
	const now = Date.now();
	for (const w of [...waiters]) {
		if (w.due > now) continue;
		waiters.delete(w);
		w.fire(now);
	}
	schedule();
}

/** Wake `fire` once at `due` (epoch ms) on the shared clock. Returns a cancel. */
export function wakeAt(due: number, fire: (now: number) => void): () => void {
	const w: Waiter = { due, fire };
	waiters.add(w);
	schedule();
	return () => {
		if (waiters.delete(w)) schedule();
	};
}

/** How many waiters the shared clock holds; for tests. */
export function pendingWakes(): number {
	return waiters.size;
}

export interface RelativeTimeProps
	extends Omit<React.ComponentProps<"time">, "children" | "dateTime"> {
	/** The stamp, epoch ms. */
	ts: number;
	mode?: RelativeTimeMode;
}

export function RelativeTime({ ts, mode = "ago", className, title, ...props }: RelativeTimeProps) {
	const valid = Number.isFinite(ts);
	const [now, setNow] = useState(() => Date.now());

	useEffect(() => {
		if (!valid) return;
		// The clock may have moved since this render's `now`; aim from the real one.
		const real = Date.now();
		if (formatRelativeTime(real - ts, mode) !== formatRelativeTime(now - ts, mode)) {
			setNow(real);
			return;
		}
		return wakeAt(ts + nextChange(real - ts, mode), setNow);
	}, [ts, mode, now, valid]);

	if (!valid) {
		return (
			<span data-slot="relative-time" className={cn("text-text-muted", className)}>
				-
			</span>
		);
	}

	return (
		<time
			data-slot="relative-time"
			data-mode={mode}
			dateTime={new Date(ts).toISOString()}
			title={title ?? formatAbsolute(ts)}
			className={cn("whitespace-nowrap tabular-nums", className)}
			{...props}
		>
			{formatRelativeTime(now - ts, mode)}
		</time>
	);
}
