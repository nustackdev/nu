// A media element as React state: one hook that binds to an <audio> or a
// <video> and hands back what it is doing and how to drive it.
//
// The element stays the source of truth. Every media event re-reads it, and
// the snapshot only changes when something on screen would, so a `progress`
// burst does not re-render the bar. `timeupdate` fires about four times a
// second, too coarse for a playhead, so while playing the time is also read
// once per animation frame.
//
// The keyboard lives on the player's root, not on the page (lib/keyboard.ts):
// spread `onKeyDown` there with a tab stop. A key a control inside has already
// handled (a slider's arrows) is left alone, and so is space or enter on a
// button, which is that button's own.

import { type KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { KeyScope } from "../keyboard";
import { bufferedEnd, clampTime, keyCommand, type MediaCommand, timeAt } from "./model";

export interface MediaSnapshot {
	/** Playing, or asked to play: false once paused or ended. */
	playing: boolean;
	ended: boolean;
	/** Asked to play but stuck for data: a stall, a seek, the first load. */
	waiting: boolean;
	/** Metadata is in: the duration and the frame size are known. */
	ready: boolean;
	/** The source failed to load or decode. */
	error: boolean;
	time: number;
	duration: number;
	/** Where the loaded run under the playhead ends. */
	buffered: number;
	volume: number;
	muted: boolean;
	rate: number;
}

export interface MediaApi extends MediaSnapshot {
	/** Callback ref for the <audio> or <video>. */
	ref: (el: HTMLMediaElement | null) => void;
	el: HTMLMediaElement | null;
	play(): void;
	pause(): void;
	toggle(): void;
	seek(t: number): void;
	seekBy(dt: number): void;
	seekFraction(f: number): void;
	setVolume(v: number): void;
	setMuted(muted: boolean): void;
	toggleMute(): void;
	setRate(r: number): void;
}

export const EMPTY_SNAPSHOT: MediaSnapshot = {
	playing: false,
	ended: false,
	waiting: false,
	ready: false,
	error: false,
	time: 0,
	duration: Number.NaN,
	buffered: 0,
	volume: 1,
	muted: false,
	rate: 1,
};

// readyState below HAVE_FUTURE_DATA: there is not enough to move forward.
const HAVE_METADATA = 1;
const HAVE_FUTURE_DATA = 3;

function read(el: HTMLMediaElement): MediaSnapshot {
	const error = el.error != null;
	const asked = !el.paused && !el.ended;
	return {
		playing: asked,
		ended: el.ended,
		waiting: !error && (el.seeking || (asked && el.readyState < HAVE_FUTURE_DATA)),
		ready: el.readyState >= HAVE_METADATA,
		error,
		time: el.currentTime,
		duration: el.duration,
		buffered: bufferedEnd(el.buffered, el.currentTime),
		volume: el.volume,
		muted: el.muted,
		rate: el.playbackRate,
	};
}

function same(a: MediaSnapshot, b: MediaSnapshot): boolean {
	for (const k in a) {
		const x = a[k as keyof MediaSnapshot];
		const y = b[k as keyof MediaSnapshot];
		if (x !== y && !(Number.isNaN(x) && Number.isNaN(y))) return false;
	}
	return true;
}

const EVENTS = [
	"loadstart",
	"loadedmetadata",
	"loadeddata",
	"durationchange",
	"canplay",
	"canplaythrough",
	"play",
	"playing",
	"pause",
	"ended",
	"waiting",
	"stalled",
	"seeking",
	"seeked",
	"timeupdate",
	"progress",
	"volumechange",
	"ratechange",
	"error",
	"emptied",
] as const;

export function useMedia(): MediaApi {
	const [el, setEl] = useState<HTMLMediaElement | null>(null);
	const [snap, setSnap] = useState<MediaSnapshot>(EMPTY_SNAPSHOT);

	useEffect(() => {
		if (!el) {
			setSnap(EMPTY_SNAPSHOT);
			return;
		}
		let frame = 0;
		const sync = () =>
			setSnap((prev) => {
				const next = read(el);
				return same(prev, next) ? prev : next;
			});
		const tick = () => {
			sync();
			frame = el.paused ? 0 : requestAnimationFrame(tick);
		};
		const onEvent = (e: Event) => {
			sync();
			if (e.type === "playing" || e.type === "play") {
				cancelAnimationFrame(frame);
				frame = requestAnimationFrame(tick);
			}
		};
		for (const name of EVENTS) el.addEventListener(name, onEvent);
		sync();
		if (!el.paused) frame = requestAnimationFrame(tick);
		return () => {
			cancelAnimationFrame(frame);
			for (const name of EVENTS) el.removeEventListener(name, onEvent);
		};
	}, [el]);

	const actions = useMemo(() => {
		const play = () => {
			if (!el) return;
			// A refused play (autoplay policy, a source that failed) is not an
			// exception worth surfacing: the element's own state says it stayed put.
			el.play()?.catch(() => {});
		};
		const pause = () => el?.pause();
		const seek = (t: number) => {
			if (el) el.currentTime = clampTime(t, el.duration);
		};
		const setVolume = (v: number) => {
			if (!el) return;
			el.volume = Math.min(1, Math.max(0, v));
			el.muted = v <= 0;
		};
		return {
			play,
			pause,
			toggle: () => {
				if (!el) return;
				if (el.paused || el.ended) play();
				else pause();
			},
			seek,
			seekBy: (dt: number) => el && seek(el.currentTime + dt),
			seekFraction: (f: number) => el && seek(timeAt(f, el.duration)),
			setVolume,
			setMuted: (muted: boolean) => {
				if (!el) return;
				el.muted = muted;
				// Unmuting at zero would be silent; come back at a level you can hear.
				if (!muted && el.volume === 0) el.volume = 0.5;
			},
			toggleMute: () => {
				if (!el) return;
				const muted = !(el.muted || el.volume === 0);
				el.muted = muted;
				if (!muted && el.volume === 0) el.volume = 0.5;
			},
			setRate: (r: number) => {
				if (el) el.playbackRate = r;
			},
		};
	}, [el]);

	return { ...snap, ...actions, ref: setEl, el };
}

export interface MediaKeyOptions {
	/** Seconds `,` and `.` step while paused: 1/fps for video. */
	fineStep: number;
	/** Called on `f`; leave it out and `f` passes through. */
	onFullscreen?: () => void;
}

const OWN_KEYS = new Set([" ", "Enter"]);

/**
 * Props for the player's root: a tab stop and the transport's keys (model.ts
 * `keyCommand`), like lib/keyboard.ts `useKeyScope`. Chords pass through, as
 * does anything a control inside already took.
 */
export function useMediaKeys(media: MediaApi, opts: MediaKeyOptions): KeyScope<HTMLElement> {
	const live = useRef({ media, opts });
	live.current = { media, opts };
	const onKeyDown = useCallback((event: KeyboardEvent<HTMLElement>) => {
		if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return;
		const target = event.target as HTMLElement;
		if (target !== event.currentTarget) {
			if (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)) return;
			if (OWN_KEYS.has(event.key) && target.closest("button, a, [role=menuitem]")) return;
		}
		const { media: m, opts: o } = live.current;
		const cmd = keyCommand(event.key, event.shiftKey, m, {
			fineStep: o.fineStep,
			fullscreen: o.onFullscreen !== undefined,
		});
		if (!cmd) return;
		event.preventDefault();
		event.stopPropagation();
		run(m, cmd, o);
	}, []);
	return { tabIndex: 0, onKeyDown };
}

function run(m: MediaApi, cmd: MediaCommand, o: MediaKeyOptions) {
	switch (cmd.kind) {
		case "toggle":
			return m.toggle();
		case "seek":
			return m.seek(cmd.to);
		case "volume":
			return m.setVolume(cmd.to);
		case "mute":
			return m.toggleMute();
		case "fullscreen":
			return o.onFullscreen?.();
	}
}
