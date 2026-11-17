// One microphone or camera, opened on request and released when done.
//
//   const dev = useCaptureDevice({ kind: "audio", constraints: (id) => ({ audio: ... }) });
//   await dev.open();       // asks permission the first time; status asking -> live | blocked
//   dev.open(otherId);      // switch device: the new stream opens, then the old one stops
//   dev.close();            // tracks stop, the light goes off; status idle
//
// Nothing opens on mount: a person's click calls `open`. The stream stops on
// `close`, on unmount, and when a newer `open` lands. Opens race (a person
// can switch twice fast): only the last one keeps its stream, the others stop
// theirs as they arrive.
//
// Device labels are empty until permission is granted, so the list is read
// again after each open and on every `devicechange` (a mic plugged in).
//
// A track that ends on its own (unplugged, permission revoked, the os took
// it) leaves the device `blocked` with `lost`. A track this hook stops itself
// fires no `ended`, so a close is never mistaken for a loss.

import * as React from "react";
import { type CaptureError, type CaptureKind, captureBlocker, mediaError } from "./support";

export type DeviceStatus = "idle" | "asking" | "live" | "blocked";

export interface CaptureDeviceOptions {
	/** Which devices the list holds: microphones or cameras. */
	kind: CaptureKind;
	/**
	 * The constraints for an open. `deviceId` is the one asked for, or null
	 * for the default (or the facing the caller wants).
	 */
	constraints: (deviceId: string | null) => MediaStreamConstraints;
	/** Called once per loss, before the status moves to blocked. */
	onLost?: () => void;
}

export interface CaptureDevice {
	status: DeviceStatus;
	error: CaptureError;
	stream: MediaStream | null;
	/** Devices of the kind, labelled once permission was granted. */
	devices: MediaDeviceInfo[];
	/** The device the open stream comes from, or null. */
	deviceId: string | null;
	/** Open (or switch to) a device. Resolves to the stream, or null when blocked or superseded. */
	open: (deviceId?: string | null) => Promise<MediaStream | null>;
	/** Stop every track. Status idle. */
	close: () => void;
}

function stopAll(stream: MediaStream | null): void {
	if (!stream) return;
	for (const t of stream.getTracks()) t.stop();
}

function trackDevice(stream: MediaStream, kind: CaptureKind): string | null {
	const track = kind === "audio" ? stream.getAudioTracks()[0] : stream.getVideoTracks()[0];
	const id = track?.getSettings?.().deviceId;
	return typeof id === "string" && id !== "" ? id : null;
}

export function useCaptureDevice(opts: CaptureDeviceOptions): CaptureDevice {
	const { kind } = opts;
	const [status, setStatus] = React.useState<DeviceStatus>("idle");
	const [error, setError] = React.useState<CaptureError>("");
	const [stream, setStream] = React.useState<MediaStream | null>(null);
	const [devices, setDevices] = React.useState<MediaDeviceInfo[]>([]);
	const [deviceId, setDeviceId] = React.useState<string | null>(null);

	// The latest options, so `open` stays stable across renders.
	const optsRef = React.useRef(opts);
	optsRef.current = opts;
	const current = React.useRef<MediaStream | null>(null);
	const ticket = React.useRef(0);
	const alive = React.useRef(true);

	const refresh = React.useCallback(async () => {
		const md = typeof navigator !== "undefined" ? navigator.mediaDevices : undefined;
		if (!md?.enumerateDevices) return;
		try {
			const all = await md.enumerateDevices();
			const want = kind === "audio" ? "audioinput" : "videoinput";
			// Before permission a browser lists one entry with no id; it is no choice.
			if (alive.current) setDevices(all.filter((d) => d.kind === want && d.deviceId !== ""));
		} catch {
			// A list we cannot read is an empty list.
		}
	}, [kind]);

	const close = React.useCallback(() => {
		ticket.current += 1;
		stopAll(current.current);
		current.current = null;
		setStream(null);
		setDeviceId(null);
		setStatus("idle");
		setError("");
	}, []);

	const open = React.useCallback(
		async (want: string | null = null): Promise<MediaStream | null> => {
			const blocker = captureBlocker(kind);
			if (blocker) {
				setStatus("blocked");
				setError(blocker);
				return null;
			}
			const mine = ++ticket.current;
			// A switch keeps the old stream live until the new one lands.
			if (!current.current) setStatus("asking");
			setError("");
			let next: MediaStream;
			try {
				next = await navigator.mediaDevices.getUserMedia(optsRef.current.constraints(want));
			} catch (err) {
				if (mine !== ticket.current || !alive.current) return null;
				stopAll(current.current);
				current.current = null;
				setStream(null);
				setDeviceId(null);
				setStatus("blocked");
				setError(mediaError(err));
				return null;
			}
			if (mine !== ticket.current || !alive.current) {
				stopAll(next);
				return null;
			}
			stopAll(current.current);
			current.current = next;
			for (const track of next.getTracks()) {
				track.addEventListener("ended", () => {
					if (current.current !== next) return;
					optsRef.current.onLost?.();
					stopAll(next);
					current.current = null;
					ticket.current += 1;
					setStream(null);
					setDeviceId(null);
					setStatus("blocked");
					setError("lost");
				});
			}
			setStream(next);
			setDeviceId(trackDevice(next, kind));
			setStatus("live");
			void refresh();
			return next;
		},
		[kind, refresh],
	);

	React.useEffect(() => {
		alive.current = true;
		const md = typeof navigator !== "undefined" ? navigator.mediaDevices : undefined;
		const onChange = () => void refresh();
		md?.addEventListener?.("devicechange", onChange);
		return () => {
			alive.current = false;
			md?.removeEventListener?.("devicechange", onChange);
			ticket.current += 1;
			stopAll(current.current);
			current.current = null;
		};
	}, [refresh]);

	return { status, error, stream, devices, deviceId, open, close };
}
