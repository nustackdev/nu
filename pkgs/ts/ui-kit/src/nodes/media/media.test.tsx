// ImageRef, VideoRef and AudioRef over the real tree store, and the scrub
// bar under video and audio: what each node draws from its props, the empty and fallback frames,
// and the slider semantics a screen reader and a keyboard get.

import { OPS } from "@nustackdev/ui-core";
import { act, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Scrubber } from "../../components/ui/media-controls";
import { NodeView, tree } from "../../tree";
import "..";
import { normAspect } from "./image";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix measures the volume slider through ResizeObserver, which jsdom lacks.
globalThis.ResizeObserver ??= class {
	observe() {}
	unobserve() {}
	disconnect() {}
};

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
});

function mount(type: string, props: Record<string, unknown>) {
	tree.getState().write([["n", type, props]]);
	act(() => root.render(<NodeView path={["n"]} />));
}

function dispatch(payload: unknown) {
	act(() => tree.getState().dispatch({ op: OPS.write, ref: ["n"], payload }));
}

const slot = (name: string) => host.querySelector<HTMLElement>(`[data-slot=${name}]`);
const cls = (el: Element | null) => el?.className.split(/\s+/) ?? [];

describe("ImageRef", () => {
	it("draws square corners until a radius is set", () => {
		mount("ImageRef", { src: "/a.png" });
		expect(cls(slot("image"))).not.toContain("rounded-md");
		dispatch({ radius: "full" });
		expect(cls(slot("image"))).toContain("rounded-full");
	});

	it("holds an aspect ratio and takes the full width for it", () => {
		mount("ImageRef", { src: "/a.png", aspect: "16:9", fit: "scale-down" });
		const img = slot("image");
		expect(img?.style.aspectRatio).toBe("16 / 9");
		expect(img?.style.width).toBe("100%");
		expect(cls(img)).toContain("object-scale-down");
	});

	it("draws a viewer with zoom on, 320px tall unless sized", () => {
		mount("ImageRef", { src: "/a.png", zoom: true });
		const viewer = slot("image-viewer");
		expect(viewer).not.toBeNull();
		expect(slot("image")).toBeNull();
		expect(cls(viewer)).toContain("h-80");
		dispatch({ aspect: "4:3" });
		expect(slot("image-viewer")?.style.aspectRatio).toBe("4 / 3");
		expect(cls(slot("image-viewer"))).not.toContain("h-80");
		dispatch({ height: 200 });
		expect(slot("image-viewer")?.style.height).toBe("200px");
		dispatch({ zoom: false });
		expect(slot("image-viewer")).toBeNull();
		expect(slot("image")).not.toBeNull();
	});

	it("fits a small image, zooms by key and goes pixelated past 1:1", () => {
		const w = vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(400);
		const h = vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(300);
		try {
			mount("ImageRef", { src: "/sprite.png", alt: "Sprite", zoom: true });
			const img = slot("image-viewer-stage")?.querySelector("img") as HTMLImageElement;
			Object.defineProperty(img, "naturalWidth", { value: 16 });
			Object.defineProperty(img, "naturalHeight", { value: 16 });
			act(() => {
				img.dispatchEvent(new Event("load"));
			});
			const zoom = () => slot("image-viewer-zoom")?.textContent;
			expect(zoom()).toBe("1875%");
			expect(img.style.width).toBe("300px");
			expect(img.style.imageRendering).toBe("pixelated");

			const stage = slot("image-viewer-stage") as HTMLElement;
			expect(stage.getAttribute("aria-label")).toBe("Sprite");
			const key = (k: string) =>
				act(() => {
					stage.dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true }));
				});
			key("1");
			expect(zoom()).toBe("100%");
			expect(img.style.imageRendering).toBe("");
			key("+");
			expect(zoom()).toBe("150%");
			key("0");
			expect(zoom()).toBe("1875%");

			const labels = [...(slot("image-viewer-controls")?.querySelectorAll("button") ?? [])].map(
				(b) => b.getAttribute("aria-label"),
			);
			expect(labels).toEqual(["Zoom out", "Zoom in", "Fit", "Actual size", "Full screen"]);
			const fit = slot("image-viewer-controls")?.querySelector('[aria-label="Fit"]');
			expect(fit?.getAttribute("aria-disabled")).toBe("true");
		} finally {
			w.mockRestore();
			h.mockRestore();
		}
	});

	it("opens full window with the exit where full screen was, and a solid close", () => {
		const w = vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(400);
		const h = vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(300);
		try {
			mount("ImageRef", { src: "/a.png", alt: "Shot", zoom: true });
			const img = slot("image-viewer-stage")?.querySelector("img") as HTMLImageElement;
			Object.defineProperty(img, "naturalWidth", { value: 800 });
			Object.defineProperty(img, "naturalHeight", { value: 600 });
			act(() => {
				img.dispatchEvent(new Event("load"));
			});
			const full = host.querySelector<HTMLElement>('[aria-label="Full screen"]');
			act(() => full?.click());
			const overlay = document.querySelector<HTMLElement>("[data-slot=image-viewer-overlay]");
			expect(overlay).not.toBeNull();
			// The full window viewer is its own viewer: its image loads again.
			const inner = overlay?.querySelector("img") as HTMLImageElement;
			Object.defineProperty(inner, "naturalWidth", { value: 800 });
			Object.defineProperty(inner, "naturalHeight", { value: 600 });
			act(() => {
				inner.dispatchEvent(new Event("load"));
			});
			const cluster = overlay?.querySelector("[data-slot=image-viewer-controls]");
			const last = [...(cluster?.querySelectorAll("button") ?? [])].at(-1);
			expect(last?.getAttribute("aria-label")).toBe("Exit full screen");
			expect(cls(cluster ?? null)).toEqual(expect.arrayContaining(["right-5", "bottom-5"]));
			const close = overlay?.querySelector("[data-slot=image-viewer-close]");
			expect(close?.getAttribute("aria-label")).toBe("Close");
			expect(cls(close ?? null)).toEqual(expect.arrayContaining(["top-5", "right-5"]));
			const stage = overlay?.querySelector("[data-slot=image-viewer-stage]") as HTMLElement;
			act(() => {
				stage.dispatchEvent(new KeyboardEvent("keydown", { key: "f", bubbles: true }));
			});
			expect(document.querySelector("[data-slot=image-viewer-overlay]")).toBeNull();
		} finally {
			w.mockRestore();
			h.mockRestore();
		}
	});

	it("reads the aspect spellings", () => {
		expect(normAspect("4/3")).toBe("4 / 3");
		expect(normAspect("1.5")).toBe("1.5");
		expect(normAspect("")).toBeUndefined();
		expect(normAspect("wide")).toBeUndefined();
		expect(normAspect("1/0")).toBeUndefined();
	});
});

describe("VideoRef", () => {
	it("draws a video with its poster, flags, ratio and corners", () => {
		mount("VideoRef", {
			src: "/clip.mp4",
			poster: "/still.jpg",
			aspect: "16:9",
			radius: "lg",
			fit: "cover",
			loop: true,
			muted: true,
		});
		const frame = slot("video");
		const video = host.querySelector("video");
		expect(video?.getAttribute("src")).toBe("/clip.mp4");
		expect(video?.getAttribute("poster")).toBe("/still.jpg");
		expect(video?.loop).toBe(true);
		expect(video?.muted).toBe(true);
		expect(video?.className).toContain("object-cover");
		expect(frame?.style.aspectRatio).toBe("16 / 9");
		expect(frame?.className).toContain("rounded-lg");
		expect(frame?.getAttribute("aria-roledescription")).toBe("video player");
		expect(frame?.tabIndex).toBe(0);
	});

	it("draws square corners and the transport until told otherwise", () => {
		mount("VideoRef", { src: "/clip.mp4" });
		expect(slot("video")?.className).toContain("rounded-none");
		expect(slot("video-controls")).not.toBeNull();
		expect(host.querySelector("[role=slider][aria-label=Seek]")).not.toBeNull();
	});

	it("says there is no video without a source, and swaps one in on a write", () => {
		mount("VideoRef", { src: "" });
		expect(host.querySelector("video")).toBeNull();
		expect(slot("empty-state")?.textContent).toContain("No video");
		dispatch({ src: "/b.mp4", width: 320 });
		expect(host.querySelector("video")?.getAttribute("src")).toBe("/b.mp4");
		expect(slot("video")?.style.width).toBe("320px");
	});
});

describe("AudioRef", () => {
	it("draws one row named by its title", async () => {
		mount("AudioRef", { src: "/a.mp3", title: "take-01.mp3", loop: true });
		const row = slot("audio");
		expect(row?.getAttribute("aria-label")).toBe("take-01.mp3");
		expect(slot("audio-title")?.textContent).toBe("take-01.mp3");
		expect(host.querySelector("audio")?.loop).toBe(true);
		expect(slot("media-play")?.getAttribute("aria-label")).toBe("Play");
		expect(slot("media-time")?.textContent).toBe("0:00 / --:--");
	});

	it("falls back to the plain bar where the waveform cannot decode", async () => {
		// jsdom has no Web Audio, so the decode comes back empty.
		mount("AudioRef", { src: "/a.mp3" });
		await act(async () => {
			await new Promise((r) => setTimeout(r, 0));
		});
		expect(slot("scrubber")).not.toBeNull();
		expect(slot("waveform")).toBeNull();
	});

	it("says there is no audio without a source", () => {
		mount("AudioRef", { title: "untitled" });
		expect(host.querySelector("audio")).toBeNull();
		expect(slot("audio")?.textContent).toContain("No audio");
		expect((slot("media-play") as HTMLButtonElement | null)?.disabled).toBe(true);
	});
});

describe("Scrubber", () => {
	function Harness() {
		const [t, setT] = useState(30);
		return <Scrubber time={t} duration={125} onSeek={setT} />;
	}

	const key = (el: Element, k: string, shift = false) =>
		act(() => {
			el.dispatchEvent(new KeyboardEvent("keydown", { key: k, shiftKey: shift, bubbles: true }));
		});

	it("is a slider that reads its time in words", () => {
		act(() => root.render(<Harness />));
		const s = slot("scrubber") as HTMLElement;
		expect(s.getAttribute("role")).toBe("slider");
		expect(s.getAttribute("aria-valuemax")).toBe("125");
		expect(s.getAttribute("aria-valuenow")).toBe("30");
		expect(s.getAttribute("aria-valuetext")).toBe("30 seconds of 2 minutes 5 seconds");
	});

	it("seeks on the arrows, shift, page keys, home and end", () => {
		act(() => root.render(<Harness />));
		const s = slot("scrubber") as HTMLElement;
		key(s, "ArrowRight");
		expect(s.getAttribute("aria-valuenow")).toBe("35");
		key(s, "ArrowLeft", true);
		expect(s.getAttribute("aria-valuenow")).toBe("20");
		key(s, "End");
		expect(s.getAttribute("aria-valuenow")).toBe("125");
		key(s, "PageDown");
		expect(s.getAttribute("aria-valuenow")).toBe("110");
		key(s, "Home");
		expect(s.getAttribute("aria-valuenow")).toBe("0");
	});

	it("is out of the tab order while the duration is unknown", () => {
		act(() => root.render(<Scrubber time={0} duration={Number.NaN} onSeek={() => {}} />));
		const s = slot("scrubber") as HTMLElement;
		expect(s.tabIndex).toBe(-1);
		expect(s.getAttribute("aria-disabled")).toBe("true");
		expect(s.getAttribute("aria-valuetext")).toBe("unknown");
	});
});
