// MicCaptureRef over the real tree store, with the jsdom fake media and XHR
// mocked. A kept take lands as the value with its meta and one change, a
// cancel keeps the old take, Delete clears it; the status notifies follow
// the device and the recorder once per move; a refusal, a lost device, a
// reset, the max duration and disabled each leave the microphone closed; and
// a pull posts the take like any picked file.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { type FakeMedia, FakeRecorder, installFakeMedia } from "../../lib/capture/fake-media";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

class FakeXHR {
	static all: FakeXHR[] = [];
	upload: { onprogress: ((e: Partial<ProgressEvent>) => void) | null } = { onprogress: null };
	onload: (() => void) | null = null;
	onerror: (() => void) | null = null;
	onabort: (() => void) | null = null;
	ontimeout: (() => void) | null = null;
	status = 0;
	responseText = "";
	method = "";
	url = "";
	body: Blob | null = null;
	aborted = false;
	open(method: string, url: string) {
		this.method = method;
		this.url = url;
	}
	send(body: Blob) {
		this.body = body;
		FakeXHR.all.push(this);
	}
	abort() {
		if (this.aborted) return;
		this.aborted = true;
		this.onabort?.();
	}
	answer(status: number, body: unknown = {}) {
		this.status = status;
		this.responseText = JSON.stringify(body);
		this.onload?.();
	}
}

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];
let media: FakeMedia;

beforeEach(() => {
	media = installFakeMedia({ mics: 2 });
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	sent = [];
	FakeXHR.all = [];
	vi.stubGlobal("XMLHttpRequest", FakeXHR);
	tree.getState().setSender((frame) => sent.push(frame));
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
	media.restore();
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
	vi.useRealTimers();
});

function mount(props: Record<string, unknown> = {}) {
	tree.getState().write([["n", "MicCaptureRef", props]]);
	act(() => root.render(<NodeView path={["n"]} />));
}

function dispatch(op: string, payload: unknown = null, id?: string) {
	act(() => tree.getState().dispatch({ op, ref: ["n"], payload, id }));
}

async function settle() {
	await act(async () => {
		for (let i = 0; i < 10; i++) await Promise.resolve();
	});
}

const notifies = () =>
	sent.filter((f) => f.op === OPS.notify).map((f) => f.payload as Record<string, unknown>);
const changes = () => notifies().filter((p) => p.event === "change").length;
const statuses = () =>
	notifies()
		.filter((p) => p.event === "status")
		.map((p) => (p.error ? `${p.status}:${p.error}` : p.status));
const value = () => tree.getState().getIn(["n"])?.props.value as Record<string, unknown> | null;

function button(name: string): HTMLButtonElement {
	const found = [...host.querySelectorAll<HTMLButtonElement>("button")].find(
		(b) => b.getAttribute("aria-label") === name || b.textContent?.trim() === name,
	);
	if (!found) throw new Error(`no button ${name}`);
	return found;
}

function click(name: string) {
	act(() => button(name).click());
}

async function record() {
	click("Record");
	await settle();
}

describe("MicCaptureRef: the take", () => {
	it("opens nothing on mount, then lands a kept take with its meta and one change", async () => {
		vi.useFakeTimers();
		mount({ label: "Memo" });
		expect(media.calls).toHaveLength(0);
		expect(value() ?? null).toBeNull();
		await record();
		expect(media.liveTracks()).toBe(1);
		act(() => vi.advanceTimersByTime(3000));
		expect(host.querySelector('[data-slot="mic-capture-time"]')?.textContent).toBe("0:03");
		click("Stop");
		const v = value();
		expect(v).toMatchObject({
			mime: "audio/webm",
			state: "picked",
			sent: 0,
			error: "",
			width: 0,
			height: 0,
		});
		expect(v?.name).toMatch(/^recording-\d{4}-\d{2}-\d{2}-\d{6}\.webm$/);
		expect(v?.duration).toBeCloseTo(3, 1);
		expect(v?.size).toBeGreaterThan(0);
		expect(changes()).toBe(1);
		expect(media.liveTracks()).toBe(0);
		expect(host.querySelector('[data-slot="audio"]')).not.toBeNull();
		expect(host.querySelector('[data-slot="mic-capture-said"]')?.textContent).toBe("Saved, 0:03");
	});

	it("keeps the old take when a new recording is canceled, and sends no change", async () => {
		mount();
		await record();
		click("Stop");
		const first = value()?.key;
		await settle();
		click("Record again");
		await settle();
		expect(button("Stop")).toBeTruthy();
		click("Cancel recording");
		expect(value()?.key).toBe(first);
		expect(changes()).toBe(1);
		expect(media.liveTracks()).toBe(0);
	});

	it("replaces the take once a new one is kept", async () => {
		mount();
		await record();
		click("Stop");
		const first = value()?.key;
		click("Record again");
		await settle();
		click("Stop");
		expect(value()?.key).not.toBe(first);
		expect(changes()).toBe(2);
	});

	it("moves focus to the main button as the row changes, and labels it", async () => {
		mount({ label: "Memo" });
		const rec = button("Record");
		expect(host.querySelector("label")?.getAttribute("for")).toBe(rec.id);
		act(() => rec.focus());
		await record();
		expect(document.activeElement).toBe(button("Stop"));
		expect(button("Stop").id).toBe(rec.id);
		click("Stop");
		expect(document.activeElement).toBe(button("Record again"));
	});

	it("deletes the take with a change", async () => {
		mount();
		await record();
		click("Stop");
		click("Delete recording");
		expect(value()).toBeNull();
		expect(changes()).toBe(2);
		expect(button("Record")).toBeTruthy();
	});
});

describe("MicCaptureRef: status", () => {
	it("says each move once: asking, live, recording, paused, recording, idle", async () => {
		mount();
		await record();
		click("Pause recording");
		click("Resume recording");
		click("Stop");
		expect(statuses()).toEqual(["asking", "live", "recording", "paused", "recording", "idle"]);
	});

	it("asks for the microphone with the processing flags and the picked device", async () => {
		mount({ processing: false });
		await record();
		expect(media.calls[0]).toEqual({
			audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
		});
		click("Stop");
		click("Record again");
		await settle();
		const second = media.calls[1].audio as MediaTrackConstraints;
		expect(second.deviceId).toEqual({ exact: "fake-mic-0" });
	});

	it("offers a microphone menu once two are known, none for one", async () => {
		mount();
		const menu = () => host.querySelector('button[aria-label^="Microphone,"]');
		expect(menu()).toBeNull();
		await record();
		expect(menu()).toBeNull();
		click("Stop");
		expect(menu()?.getAttribute("aria-label")).toBe("Microphone, Built-in microphone");
		act(() => media.setDevices(1, 0));
		await settle();
		expect(menu()).toBeNull();
	});

	it("is blocked with denied when refused, with no stream left and a retry", async () => {
		media.setFail("denied");
		mount();
		await record();
		expect(statuses()).toEqual(["asking", "blocked:denied"]);
		expect(media.liveTracks()).toBe(0);
		expect(host.querySelector('[data-slot="mic-capture-reason"]')?.textContent).toContain(
			"site settings",
		);
		media.setFail("");
		click("Try again");
		await settle();
		expect(statuses().slice(2)).toEqual(["asking", "live", "recording"]);
	});

	it("keeps what was recorded when the device is lost mid take", async () => {
		mount();
		await record();
		act(() => media.lose());
		expect(value()).toMatchObject({ mime: "audio/webm" });
		expect(changes()).toBe(1);
		expect(statuses().at(-1)).toBe("blocked:lost");
		expect(host.querySelector('[data-slot="mic-capture-reason"]')?.textContent).toContain(
			"disconnected",
		);
		expect(host.querySelector('[data-slot="audio"]')).not.toBeNull();
	});
});

describe("MicCaptureRef: the device closes", () => {
	it("on reset: the take goes, the tracks stop, no change, status idle", async () => {
		mount();
		await record();
		click("Stop");
		click("Record again");
		await settle();
		expect(media.liveTracks()).toBe(1);
		dispatch("reset");
		await settle();
		expect(value()).toBeNull();
		expect(media.liveTracks()).toBe(0);
		expect(changes()).toBe(1);
		expect(statuses().at(-1)).toBe("idle");
		expect(button("Record")).toBeTruthy();
	});

	it("at max_duration, keeping the take", async () => {
		vi.useFakeTimers();
		mount({ max_duration: 2 });
		expect(host.textContent).toContain("Up to 0:02");
		await record();
		expect(host.querySelector('[data-slot="mic-capture-time"]')?.textContent).toBe("0:00 / 0:02");
		act(() => vi.advanceTimersByTime(2500));
		expect(value()?.duration).toBe(2);
		expect(changes()).toBe(1);
		expect(media.liveTracks()).toBe(0);
		expect(statuses().at(-1)).toBe("idle");
	});

	it("when disabled: a recording stops and is kept, nothing works after", async () => {
		mount();
		await record();
		dispatch(OPS.write, { disabled: true });
		expect(media.liveTracks()).toBe(0);
		expect(value()).not.toBeNull();
		expect(statuses().at(-1)).toBe("idle");
		expect(button("Record again").disabled).toBe(true);
	});

	it("never takes a value from the program", () => {
		mount();
		dispatch(OPS.write, { value: { name: "fake" }, label: "Memo" });
		expect(value() ?? null).toBeNull();
		expect(host.textContent).toContain("Memo");
	});
});

describe("MicCaptureRef: the program reads the take", () => {
	it("pulls the take over http and answers upload landed", async () => {
		mount();
		await record();
		click("Stop");
		const v = value();
		dispatch("pull", { key: null, rid: "r1", url: "/_nu/upload/sid1" });
		expect(FakeXHR.all).toHaveLength(1);
		expect(FakeXHR.all[0].body?.size).toBe(v?.size);
		FakeXHR.all[0].answer(201, { token: "t".repeat(32), size: v?.size });
		await settle();
		expect(notifies().find((p) => p.event === "upload")).toMatchObject({
			key: v?.key,
			rid: "r1",
			state: "landed",
			token: "t".repeat(32),
		});
		expect(value()).toMatchObject({ state: "landed", duration: v?.duration });
	});

	it("reads null empty and the take once kept", async () => {
		mount();
		dispatch(OPS.read, null, "r");
		expect(sent.at(-1)).toMatchObject({ op: OPS.read, id: "r", payload: null });
		await record();
		click("Stop");
		dispatch(OPS.read, null, "r2");
		expect(sent.at(-1)?.payload).toEqual(value());
		expect(FakeRecorder.last).not.toBeNull();
	});
});
