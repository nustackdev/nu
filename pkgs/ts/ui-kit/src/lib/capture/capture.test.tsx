// The shared capture layer over the jsdom fakes: the support helpers, a
// device that opens, switches, is refused, lost and released, and a recorder
// that pauses out of its time, stops at its max and keeps a take cut short.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { type FakeMedia, installFakeMedia } from "./fake-media";
import {
	bareMime,
	blockedText,
	canRetry,
	captureBlocker,
	extension,
	mediaError,
	recorderMime,
	takeName,
} from "./support";
import { type CaptureDevice, useCaptureDevice } from "./use-capture-device";
import { type RecordedTake, type Recorder, useRecorder } from "./use-recorder";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let media: FakeMedia;
let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	media = installFakeMedia({ mics: 2, cameras: 2 });
	host = document.createElement("div");
	document.body.append(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	media.restore();
	vi.useRealTimers();
});

describe("support", () => {
	it("names takes from local time with the mime's extension", () => {
		const at = new Date(2026, 10, 17, 14, 3, 22);
		expect(takeName("recording", "audio/webm;codecs=opus", at)).toBe(
			"recording-2026-11-17-140322.webm",
		);
		expect(takeName("photo", "image/jpeg", at)).toBe("photo-2026-11-17-140322.jpg");
		expect(extension("audio/mp4")).toBe("m4a");
		expect(extension("x/unknown")).toBe("bin");
		expect(bareMime("Video/MP4; codecs=avc1")).toBe("video/mp4");
	});

	it("folds getUserMedia errors into codes", () => {
		expect(mediaError({ name: "NotAllowedError" })).toBe("denied");
		expect(mediaError({ name: "NotFoundError" })).toBe("no_device");
		expect(mediaError({ name: "OverconstrainedError" })).toBe("no_device");
		expect(mediaError({ name: "NotReadableError" })).toBe("busy");
		expect(mediaError(new Error("x"))).toBe("failed");
		expect(canRetry("denied")).toBe(true);
		expect(canRetry("insecure")).toBe(false);
		expect(blockedText("Microphone", "no_device")).toBe(
			"No microphone found. Connect one, then try again.",
		);
	});

	it("picks the first mime the recorder makes", () => {
		expect(recorderMime("audio")).toBe("audio/webm;codecs=opus");
		expect(recorderMime("video")).toBe("video/webm;codecs=vp9,opus");
	});

	it("says why a page cannot capture", () => {
		expect(captureBlocker("audio")).toBe("");
		Object.defineProperty(window, "isSecureContext", { value: false, configurable: true });
		expect(captureBlocker("audio")).toBe("insecure");
	});
});

function mountDevice(kind: "audio" | "video" = "audio"): { current: CaptureDevice } {
	const out = {} as { current: CaptureDevice };
	function Probe() {
		out.current = useCaptureDevice({
			kind,
			constraints: (id) =>
				kind === "audio"
					? { audio: id ? { deviceId: { exact: id } } : true }
					: { video: id ? { deviceId: { exact: id } } : true },
		});
		return null;
	}
	act(() => root.render(<Probe />));
	return out;
}

describe("useCaptureDevice", () => {
	it("opens nothing until asked, then opens and lists labelled devices", async () => {
		const dev = mountDevice();
		expect(dev.current.status).toBe("idle");
		expect(media.calls).toHaveLength(0);
		await act(async () => {
			await dev.current.open();
		});
		expect(dev.current.status).toBe("live");
		expect(dev.current.deviceId).toBe("fake-mic-0");
		expect(dev.current.devices.map((d) => d.label)).toEqual([
			"Built-in microphone",
			"USB microphone 1",
		]);
		expect(media.liveTracks()).toBe(1);
	});

	it("switches device and stops the old stream", async () => {
		const dev = mountDevice();
		await act(async () => {
			await dev.current.open();
		});
		await act(async () => {
			await dev.current.open("fake-mic-1");
		});
		expect(dev.current.deviceId).toBe("fake-mic-1");
		expect(media.liveTracks()).toBe(1);
	});

	it("is blocked with a code when refused", async () => {
		media.setFail("denied");
		const dev = mountDevice();
		await act(async () => {
			await dev.current.open();
		});
		expect(dev.current.status).toBe("blocked");
		expect(dev.current.error).toBe("denied");
		expect(dev.current.stream).toBeNull();
	});

	it("is blocked with lost when the device goes away, not when closed", async () => {
		const dev = mountDevice();
		await act(async () => {
			await dev.current.open();
		});
		act(() => dev.current.close());
		expect(dev.current.status).toBe("idle");
		expect(dev.current.error).toBe("");
		expect(media.liveTracks()).toBe(0);
		await act(async () => {
			await dev.current.open();
		});
		act(() => media.lose());
		expect(dev.current.status).toBe("blocked");
		expect(dev.current.error).toBe("lost");
	});

	it("releases the device on unmount", async () => {
		const dev = mountDevice("video");
		await act(async () => {
			await dev.current.open();
		});
		expect(media.liveTracks()).toBe(1);
		act(() => root.render(null));
		expect(media.liveTracks()).toBe(0);
	});
});

function mountRecorder(): { current: Recorder } {
	const out = {} as { current: Recorder };
	function Probe() {
		out.current = useRecorder();
		return null;
	}
	act(() => root.render(<Probe />));
	return out;
}

async function stream(): Promise<MediaStream> {
	return navigator.mediaDevices.getUserMedia({ audio: true });
}

describe("useRecorder", () => {
	it("records, leaves pauses out of the time, and hands the take over", async () => {
		vi.useFakeTimers();
		const rec = mountRecorder();
		const s = await stream();
		const takes: Array<RecordedTake | null> = [];
		act(() => {
			rec.current.start(s, { mime: recorderMime("audio"), onDone: (t) => takes.push(t) });
		});
		expect(rec.current.state).toBe("recording");
		act(() => vi.advanceTimersByTime(2000));
		act(() => rec.current.pause());
		expect(rec.current.state).toBe("paused");
		act(() => vi.advanceTimersByTime(5000));
		act(() => rec.current.resume());
		act(() => vi.advanceTimersByTime(1000));
		act(() => rec.current.stop());
		expect(rec.current.state).toBe("inactive");
		expect(takes).toHaveLength(1);
		const take = takes[0];
		expect(take?.mime).toBe("audio/webm");
		expect(take?.blob.size).toBeGreaterThan(0);
		expect(take?.duration).toBeGreaterThan(2.9);
		expect(take?.duration).toBeLessThan(3.2);
	});

	it("stops itself at the max duration", async () => {
		vi.useFakeTimers();
		const rec = mountRecorder();
		const s = await stream();
		const takes: Array<RecordedTake | null> = [];
		act(() => {
			rec.current.start(s, { mime: "", maxSeconds: 2, onDone: (t) => takes.push(t) });
		});
		act(() => vi.advanceTimersByTime(2500));
		expect(rec.current.state).toBe("inactive");
		expect(takes).toHaveLength(1);
		expect(takes[0]?.duration).toBe(2);
	});

	it("keeps a take cut short by a lost device, and drops a canceled one", async () => {
		const rec = mountRecorder();
		const takes: Array<RecordedTake | null> = [];
		const s1 = await stream();
		act(() => {
			rec.current.start(s1, { mime: "", onDone: (t) => takes.push(t) });
		});
		act(() => media.lose());
		expect(takes).toHaveLength(1);
		expect(takes[0]?.blob.size).toBeGreaterThan(0);

		const s2 = await stream();
		act(() => {
			rec.current.start(s2, { mime: "", onDone: (t) => takes.push(t) });
		});
		act(() => rec.current.cancel());
		expect(rec.current.state).toBe("inactive");
		expect(takes).toHaveLength(1);
	});
});
