// CameraCaptureRef over the real tree store, with the jsdom fake cameras.
// Nothing opens on mount; open goes asking then live; a photo and a video
// land as the value with their meta and one change, and close the camera;
// cancel and close keep the old take; flip asks the other facing; a refusal,
// a lost camera, a hidden tab and a reset each leave the camera as the
// contract says; and a take pulls like any picked file.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { type FakeMedia, installFakeMedia } from "../../lib/capture/fake-media";
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
	open(method: string, url: string) {
		this.method = method;
		this.url = url;
	}
	send(body: Blob) {
		this.body = body;
		FakeXHR.all.push(this);
	}
	abort() {
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
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	sent = [];
	FakeXHR.all = [];
	media = installFakeMedia({ cameras: 2, plain: true });
	vi.stubGlobal("XMLHttpRequest", FakeXHR);
	// jsdom draws nothing: a canvas that hands back a few bytes of the asked type.
	vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(
		() => ({ drawImage: () => {} }) as unknown as CanvasRenderingContext2D,
	);
	vi.spyOn(HTMLCanvasElement.prototype, "toBlob").mockImplementation(function (
		this: HTMLCanvasElement,
		cb: BlobCallback,
		type?: string,
	) {
		cb(new Blob([new Uint8Array(32)], { type: type ?? "image/png" }));
	});
	let n = 0;
	URL.createObjectURL = vi.fn(() => `blob:take-${++n}`);
	URL.revokeObjectURL = vi.fn();
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

function draw(props: Record<string, unknown> = {}) {
	tree.getState().write([["n", "CameraCaptureRef", props]]);
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
const events = (event: string) => notifies().filter((p) => p.event === event);
const statuses = () => events("status").map((p) => (p.error ? `${p.status}:${p.error}` : p.status));
const changes = () => events("change").length;
const value = () =>
	(tree.getState().getIn(["n"])?.props.value ?? null) as Record<string, unknown> | null;

function button(label: string): HTMLButtonElement {
	const found =
		host.querySelector<HTMLButtonElement>(`button[aria-label="${label}"]`) ??
		[...host.querySelectorAll<HTMLButtonElement>("button")].find(
			(b) => b.textContent?.trim() === label,
		);
	if (!found) throw new Error(`no button ${label}`);
	return found;
}

async function click(label: string) {
	const b = button(label);
	await act(async () => b.click());
	await settle();
}

async function openLive(props: Record<string, unknown> = {}) {
	draw(props);
	await click("Open camera");
	expect(host.querySelector("[data-slot='camera-preview']")).not.toBeNull();
}

async function photo() {
	await openLive();
	await click("Take photo");
}

describe("CameraCaptureRef: photo", () => {
	it("opens nothing on mount, then asks and goes live with a mirrored preview", async () => {
		media.restore();
		media = installFakeMedia({ cameras: 2, plain: true, delayMs: 30 });
		draw({ label: "Selfie" });
		expect(media.calls).toHaveLength(0);
		expect(value()).toBeNull();
		const open = button("Open camera");
		expect(host.querySelector("label")?.getAttribute("for")).toBe(open.id);
		act(() => open.click());
		expect(host.textContent).toContain("Waiting for the camera");
		await act(async () => new Promise((r) => setTimeout(r, 50)));
		await settle();
		const preview = host.querySelector<HTMLVideoElement>("[data-slot='camera-preview']");
		expect(preview?.srcObject).toBeTruthy();
		expect(preview?.className).toContain("-scale-x-100");
		expect(statuses()).toEqual(["asking", "live"]);
		expect(media.calls[0]).toEqual({
			video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: { ideal: "user" } },
			audio: false,
		});
		expect(media.liveTracks()).toBe(1);
		expect(host.querySelector("[aria-live='polite']")?.textContent).toContain("Camera on");
	});

	it("lands a photo with its size and one change, and closes the camera", async () => {
		await photo();
		expect(value()).toMatchObject({
			mime: "image/jpeg",
			size: 32,
			state: "picked",
			duration: 0,
			width: 1280,
			height: 720,
		});
		expect(String(value()?.name)).toMatch(/^photo-\d{4}-\d{2}-\d{2}-\d{6}\.jpg$/);
		expect(changes()).toBe(1);
		expect(media.liveTracks()).toBe(0);
		expect(statuses()).toEqual(["asking", "live", "idle"]);
		expect(host.querySelector("img")?.getAttribute("src")).toBe("blob:take-1");
		expect(button("Retake")).toBeTruthy();
	});

	it("encodes the asked format", async () => {
		await openLive({ format: "webp" });
		await click("Take photo");
		expect(value()).toMatchObject({ mime: "image/webp" });
		expect(String(value()?.name)).toMatch(/\.webp$/);
	});

	it("keeps the old take on a retake that is closed, and deletes with a change", async () => {
		await photo();
		const key = value()?.key;
		await click("Retake");
		expect(media.liveTracks()).toBe(1);
		await click("Close camera");
		expect(value()?.key).toBe(key);
		expect(changes()).toBe(1);
		expect(media.liveTracks()).toBe(0);
		await click("Delete");
		expect(value()).toBeNull();
		expect(changes()).toBe(2);
		expect(button("Open camera")).toBeTruthy();
	});

	it("flips to the other facing and stops the old tracks", async () => {
		await openLive();
		expect(button("Switch camera")).toBeTruthy();
		expect(button("Choose camera")).toBeTruthy();
		await click("Switch camera");
		expect(media.calls.at(-1)).toMatchObject({ video: { facingMode: { ideal: "environment" } } });
		expect(media.liveTracks()).toBe(1);
		const preview = host.querySelector<HTMLVideoElement>("[data-slot='camera-preview']");
		expect(preview?.className).not.toContain("-scale-x-100");
		expect(statuses()).toEqual(["asking", "live"]);
	});

	it("shows no flip or menu with one camera", async () => {
		media.restore();
		media = installFakeMedia({ cameras: 1, plain: true });
		await openLive();
		expect(host.querySelector("button[aria-label='Switch camera']")).toBeNull();
		expect(host.querySelector("button[aria-label='Choose camera']")).toBeNull();
	});

	it("is blocked with denied, and tries again", async () => {
		media.setFail("denied");
		draw();
		await click("Open camera");
		expect(statuses()).toEqual(["asking", "blocked:denied"]);
		expect(host.textContent).toContain("Camera access is blocked");
		media.setFail("");
		await click("Try again");
		expect(statuses().at(-1)).toBe("live");
	});

	it("is blocked with lost when the camera goes while live, with no take", async () => {
		await openLive();
		act(() => media.lose());
		expect(statuses().at(-1)).toBe("blocked:lost");
		expect(value()).toBeNull();
		expect(changes()).toBe(0);
	});

	it("closes when the tab hides while live", async () => {
		await openLive();
		Object.defineProperty(document, "visibilityState", { value: "hidden", configurable: true });
		act(() => {
			document.dispatchEvent(new Event("visibilitychange"));
		});
		delete (document as { visibilityState?: unknown }).visibilityState;
		expect(media.liveTracks()).toBe(0);
		expect(statuses().at(-1)).toBe("idle");
	});

	it("resets to no take, closes the camera, and sends no change", async () => {
		await photo();
		await click("Retake");
		expect(media.liveTracks()).toBe(1);
		dispatch("reset");
		await settle();
		expect(value()).toBeNull();
		expect(media.liveTracks()).toBe(0);
		expect(changes()).toBe(1);
		expect(statuses().at(-1)).toBe("idle");
	});

	it("pulls a take like a picked file", async () => {
		await photo();
		dispatch("pull", { key: null, rid: "r1", url: "/_nu/upload/sid1" });
		const xhr = FakeXHR.all[0];
		expect(xhr?.method).toBe("POST");
		expect(xhr?.body?.size).toBe(32);
		act(() => xhr?.answer(201, { token: "a".repeat(32), size: 32 }));
		await settle();
		expect(events("upload")).toEqual([
			{
				event: "upload",
				key: value()?.key,
				rid: "r1",
				token: "a".repeat(32),
				state: "landed",
				size: 32,
				error: "",
			},
		]);
		expect(value()).toMatchObject({ state: "landed", width: 1280 });
	});
});

describe("CameraCaptureRef: video", () => {
	async function recording(props: Record<string, unknown> = {}) {
		vi.useFakeTimers();
		await openLive({ mode: "video", ...props });
		await click("Start recording");
	}

	it("records with sound, pauses out of the time, and stops with a take", async () => {
		await recording();
		expect(media.calls[0]).toMatchObject({ audio: true });
		expect(statuses()).toEqual(["asking", "live", "recording"]);
		expect(host.querySelector("button[aria-label='Switch camera']")).toBeNull();
		act(() => vi.advanceTimersByTime(2000));
		expect(host.querySelector("[data-slot='camera-time']")?.textContent).toContain("0:02");
		await click("Pause recording");
		act(() => vi.advanceTimersByTime(5000));
		await click("Resume recording");
		act(() => vi.advanceTimersByTime(1000));
		await click("Stop and keep");
		expect(statuses()).toEqual(["asking", "live", "recording", "paused", "recording", "idle"]);
		expect(value()).toMatchObject({ mime: "video/webm", width: 1280, height: 720 });
		expect(Number(value()?.duration)).toBeGreaterThan(2.9);
		expect(Number(value()?.duration)).toBeLessThan(3.2);
		expect(String(value()?.name)).toMatch(/^video-.*\.webm$/);
		expect(changes()).toBe(1);
		expect(media.liveTracks()).toBe(0);
	});

	it("records video only with audio off, and stops itself at the max", async () => {
		await recording({ audio: false, max_duration: 2 });
		expect(media.calls[0]).toMatchObject({ audio: false });
		expect(host.querySelector("[data-slot='camera-time']")?.textContent).toContain("0:00 / 0:02");
		act(() => vi.advanceTimersByTime(2500));
		await settle();
		expect(value()).toMatchObject({ duration: 2 });
		expect(changes()).toBe(1);
	});

	it("drops a discarded recording and keeps the old take, with no change", async () => {
		await recording();
		act(() => vi.advanceTimersByTime(1000));
		await click("Stop and keep");
		const key = value()?.key;
		await click("Retake");
		await click("Start recording");
		await click("Discard recording");
		expect(value()?.key).toBe(key);
		expect(changes()).toBe(1);
		expect(media.liveTracks()).toBe(0);
	});

	it("keeps what was recorded when the camera goes mid take", async () => {
		await recording();
		act(() => vi.advanceTimersByTime(1000));
		act(() => media.lose());
		await settle();
		expect(value()).toMatchObject({ mime: "video/webm" });
		expect(changes()).toBe(1);
		expect(statuses().at(-1)).toBe("blocked:lost");
		expect(button("Back to the video")).toBeTruthy();
	});

	it("stops and keeps a recording when disabled, and closes the camera", async () => {
		await recording();
		act(() => vi.advanceTimersByTime(1000));
		dispatch("write", { disabled: true });
		await settle();
		expect(value()).toMatchObject({ mime: "video/webm" });
		expect(changes()).toBe(1);
		expect(media.liveTracks()).toBe(0);
		expect(statuses().at(-1)).toBe("idle");
	});

	it("resets mid recording: no take, camera closed, idle, no change", async () => {
		await recording();
		act(() => vi.advanceTimersByTime(1000));
		dispatch("reset");
		await settle();
		expect(value()).toBeNull();
		expect(changes()).toBe(0);
		expect(media.liveTracks()).toBe(0);
		expect(statuses().at(-1)).toBe("idle");
	});

	it("does not close on a hidden tab while recording", async () => {
		await recording();
		Object.defineProperty(document, "visibilityState", { value: "hidden", configurable: true });
		act(() => {
			document.dispatchEvent(new Event("visibilitychange"));
		});
		delete (document as { visibilityState?: unknown }).visibilityState;
		expect(media.liveTracks()).toBe(2);
		expect(statuses().at(-1)).toBe("recording");
	});

	it("reopens with sound on a mode change while live, keeping it live", async () => {
		await openLive();
		expect(media.calls[0]).toMatchObject({ audio: false });
		dispatch("write", { mode: "video" });
		await settle();
		expect(media.calls.at(-1)).toMatchObject({ audio: true });
		expect(media.liveTracks()).toBe(2);
		expect(statuses()).toEqual(["asking", "live"]);
	});
});
